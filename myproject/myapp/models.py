from django.db import models

class Article(models.Model):
    title = models.CharField(max_length=255, unique=True)
    datetime = models.DateTimeField()
    article_text = models.TextField()
    source = models.CharField(max_length=255)

    def __str__(self):
        return self.title