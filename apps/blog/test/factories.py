import factory
from django.utils.text import slugify
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.blog.models import Post, Comment, Category, Media
from apps.users.test.factories import UserFactory

class CategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Category

    name = factory.Sequence(lambda n: f"Category {n}")
    slug = factory.LazyAttribute(lambda obj: slugify(obj.name))

class PostFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Post

    title = factory.Faker("sentence")
    content = factory.Faker("text")
    author = factory.SubFactory(UserFactory)

    @factory.post_generation
    def categories(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for category in extracted:
                self.categories.add(category)

class CommentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Comment

    content = factory.Faker("sentence")
    author = factory.SubFactory(UserFactory)
    post = factory.SubFactory(PostFactory)

class MediaFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Media

    post = factory.SubFactory(PostFactory)
    file = factory.LazyAttribute(lambda x: SimpleUploadedFile(
        "test.jpg",
        b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xFF\xFF\xFF\x21\xF9\x04\x00\x00\x00\x00\x00\x2C\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x4C\x01\x00\x3B",
        content_type="image/gif"
    ))
    type = "image"
