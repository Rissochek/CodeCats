from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Article
from django.db import IntegrityError

@csrf_exempt
def save_articles(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            success_count = 0
            errors = []

            for item in data:
                try:
                    # Пытаемся создать запись
                    Article.objects.create(
                        title=item['title'],
                        datetime=item['datetime'],
                        article_text=item['article_text'],
                        source=item['source']
                    )
                    success_count += 1
                except IntegrityError as e:
                    # Ловим ошибку уникальности
                    errors.append({
                        'title': item['title'],
                        'error': str(e)
                    })
                except Exception as e:
                    # Ловим другие ошибки
                    errors.append({
                        'title': item['title'],
                        'error': str(e)
                    })

            # Возвращаем результат
            return JsonResponse({
                'status': 'success',
                'success_count': success_count,
                'errors': errors
            }, status=200)

        except Exception as e:
            # Обработка ошибок парсинга JSON
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)