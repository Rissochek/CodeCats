import os
import json
import pickle
import joblib
import numpy as np
import pandas as pd
from typing import List, Optional

from sklearn.preprocessing import MinMaxScaler
from scipy.fft import fft


def load_sentiment_features(
    df: pd.DataFrame,
    sentiment_json_path: str,
    scale_factor: int = 1000
) -> pd.DataFrame:
    # (как было) ...
    with open(sentiment_json_path, 'r', encoding='utf-8') as f:
        sent_df = pd.DataFrame(json.load(f))
    sent_df['date'] = pd.to_datetime(sent_df['date']).dt.date
    sent_df['answer'] = sent_df['answer'].astype(int)
    stats = (
        sent_df[sent_df['sphere'].isin(['Финансы', 'Энергетика'])]
        .groupby(['date', 'sphere'])['answer']
        .agg(['mean', 'std', 'min', 'max', 'count', 'skew'])
        .reset_index()
    )
    stats['daily_range'] = stats['max'] - stats['min']
    stats['cv'] = stats['std'] / stats['mean'].replace(0, 1e-8)
    fin = stats[stats['sphere']=='Финансы'].drop('sphere',1)
    en  = stats[stats['sphere']=='Энергетика'].drop('sphere',1)
    fin.columns = ['date'] + [f'financial_{c}' for c in fin.columns[1:]]
    en.columns  = ['date'] + [f'energetic_{c}' for c in en.columns[1:]]
    df['date'] = pd.to_datetime(df['begin']).dt.date
    df = df.merge(fin, on='date', how='left')
    df = df.merge(en,  on='date', how='left')
    for col in df.columns:
        if col.startswith(('financial_','energetic_')):
            df[col] = df[col].fillna(0)*scale_factor
    df.drop('date',axis=1,inplace=True)
    return df


def add_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    # as before
    df = df.copy()
    df['begin'] = pd.to_datetime(df['begin'])
    df.set_index('begin', inplace=True)
    price_cols = ['open','high','low','close','market_open','market_close_pred','market_high','market_low']
    zero_cols  = ['volume','value','market_volume','market_value']
    df[price_cols] = df[price_cols].ffill()
    df[zero_cols]  = df[zero_cols].fillna(0)
    idx = df.index
    df['day_sin']  = np.sin(2*np.pi*idx.dayofweek/7)
    df['day_cos']  = np.cos(2*np.pi*idx.dayofweek/7)
    df['hour_sin'] = np.sin(2*np.pi*idx.hour/24)
    df['hour_cos'] = np.cos(2*np.pi*idx.hour/24)
    windows=[5,10,15,30,50]
    for w in windows:
        df[f'open_ma_{w}']=df['open'].rolling(w).mean().fillna(0)
        df[f'open_var_{w}']=df['open'].rolling(w).var().fillna(0)
        df[f'close_ma_{w}']=df['close'].shift(1).rolling(w).mean().fillna(0)
        df[f'close_var_{w}']=df['close'].shift(1).rolling(w).var().fillna(0)
        df[f'vol_ma_{w}']=df['volume'].rolling(w).mean().fillna(0)
        df[f'vol_var_{w}']=df['volume'].rolling(w).var().fillna(0)
        df[f'val_ma_{w}']=df['value'].rolling(w).mean().fillna(0)
        df[f'val_var_{w}']=df['value'].rolling(w).var().fillna(0)
    lags=[1,5,14,30]
    for lag in lags:
        df[f'open_lag_{lag}']=df['open'].shift(lag).fillna(0)
        df[f'close_lag_{lag}']=df['close'].shift(lag).fillna(0)
        df[f'vol_lag_{lag}']=df['volume'].shift(lag).fillna(0)
        df[f'val_lag_{lag}']=df['value'].shift(lag).fillna(0)
    df['vol_vs_mkt']=df['volume']/df['market_volume'].replace(0,1)
    df['val_vs_mkt']=df['value']/df['market_value'].replace(0,1)
    df['open_vs_mkt']=df['open']-df['market_open']
    df['open_mkt_ma5']=df['open_vs_mkt'].rolling(5).mean().fillna(0)
    df['vol_mkt_corr30']=df['volume'].rolling(30).corr(df['market_volume']).fillna(0)
    df['vol_ratio30']=df['close'].rolling(30).std()/df['market_close_pred'].rolling(30).std().replace(0,1)
    df.replace([np.inf,-np.inf],0,inplace=True)
    df.fillna(0,inplace=True)
    df.reset_index(inplace=True)
    return df

class PredictiveModel:
    """
    Инициализация:
      model_name: название без суффикса
      models_folder: путь к папке
      window_size: (опционально) размер окна
      history_size: (опционально) максимальная длина df
    """
    def __init__(
        self,
        model_name: str,
        models_folder: str = 'predictive_models',
        window_size: Optional[int] = 31,
        history_size: Optional[int] = None
    ):
        # путь по __file__
        base = os.path.dirname(__file__)
        folder = os.path.join(base, models_folder)
        self.name = model_name.upper()
        # поиск файла
        for ext in ('.pkl','.joblib'):
            path = os.path.join(folder, f"{self.name}_predictive_model{ext}")
            if os.path.exists(path):
                self.model_path = path
                self.ext = ext
                break
        else:
            raise FileNotFoundError(f"Модель {self.name} не найдена в {folder}")
        # загрузка
        if self.ext == '.pkl':
            with open(self.model_path,'rb') as f:
                self.model = pickle.load(f)
        else:
            self.model = joblib.load(self.model_path)
        # проверка predict
        if not hasattr(self.model,'predict'):
            raise AttributeError('Отсутствует метод predict')
        # window_size
        if window_size is not None:
            self.model.window_size = window_size
        if not hasattr(self.model,'window_size'):
            raise AttributeError('Укажите window_size или добавьте атрибут в модель')
        # history_size
        if history_size is not None:
            self.history_size = history_size
        else:
            self.history_size = getattr(self.model,'history_size', self.model.window_size*10)

    def predict_next(
        self,
        df: pd.DataFrame,
        column: str = 'close',
        sentiment_json_path: Optional[str] = None
    ) -> List[float]:
        # обрезка
        if len(df)>self.history_size:
            df = df.tail(self.history_size)
        df['begin'] = pd.to_datetime(df['begin'])
        df['end'] = pd.to_datetime(df['end'])
        df = df.sort_values('begin')
        print(df.columns)

        market_agg = df.groupby('begin').agg({
            'volume': 'sum',
            'value': 'sum',
            'open': 'mean',
            'close': 'mean',
            'high': 'max',
            'low': 'min'
        }).reset_index()
        market_agg.columns = ['begin', 'market_volume', 'market_value', 'market_open', 'market_close_pred', 'market_high', 'market_low']
        df = df.merge(market_agg, on='begin', how='left')

        df['day_sin'] = np.sin(2 * np.pi * df['begin'].dt.dayofweek / 7)
        df['day_cos'] = np.cos(2 * np.pi * df['begin'].dt.dayofweek / 7)
        df['hour_sin'] = np.sin(2 * np.pi * df['begin'].dt.hour / 24)
        df['hour_cos'] = np.cos(2 * np.pi * df['begin'].dt.hour / 24)

        df = df.replace([np.inf, -np.inf], np.nan)
        df = df.fillna(0)
        if sentiment_json_path:
            df = load_sentiment_features(df, sentiment_json_path)
        # тех. инд
        df = add_technical_indicators(df)
        # ряд
        if column not in df.columns:
            raise ValueError(f"Колонка {column} отсутствует")
        series = df[column].values
        if len(series)<self.model.window_size:
            raise ValueError(f"Нужно >={self.model.window_size} точек для предсказания")
        window = series[-self.model.window_size:].astype(float).copy()
        preds=[]
        for _ in range(5):
            x=window.reshape(1,-1)
            p=self.model.predict(x)[0]
            preds.append(float(p))
            window=np.roll(window,-1)
            window[-1]=p
        return preds


data = {
    "begin": pd.to_datetime([
        "2025-01-01 10:00", 
        "2025-01-02 10:00", 
        "2025-01-03 10:00", 
        "2025-01-04 10:00", 
        "2025-01-05 10:00"
    ]),
    "open":   [100.5, 101.2, 102.0, 103.5, 104.1],
    "high":   [101.0, 101.8, 102.5, 104.0, 104.6],
    "low":    [99.8, 100.9, 101.7, 103.0, 103.7],
    "close":  [100.9, 101.5, 102.3, 103.8, 104.3],
    "volume": [1500, 1800, 1700, 1600, 1550],
    "value":  [151000, 182700, 174910, 165760, 161665],
    "company": ["SBER", "SBER", "SBER", "SBER", "SBER"]
}

df_example = pd.DataFrame(data)
pm = PredictiveModel('SBER')
pm.predict_next(df_example)