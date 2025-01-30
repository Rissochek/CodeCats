from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Article

@csrf_exempt
def save_articles(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            for item in data:
                Article.objects.create(
                    title=item['title'],
                    datetime=item['datetime'],
                    article_text=item['article_text'],
                    source=item['source']
                )
            return JsonResponse({'status': 'success'}, status=201)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)