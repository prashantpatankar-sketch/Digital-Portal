# 📚 Django Project Setup: Step-by-Step Example

## Complete Walkthrough: Creating a Blog Project

### Step 1: Create the Django Project

```bash
# Create project directory
django-admin startproject myblog

# Navigate to project
cd myblog

# Verify structure
ls -la
```

**Output:**
```
manage.py
myblog/
├── __init__.py
├── settings.py
├── urls.py
├── asgi.py
└── wsgi.py
```

---

### Step 2: Create the Blog App

```bash
python manage.py startapp blog
```

**Output:**
```
blog/
├── migrations/
│   └── __init__.py
├── __init__.py
├── admin.py
├── apps.py
├── models.py
├── tests.py
├── views.py
└── urls.py
```

---

### Step 3: Define Database Models

**Edit: `blog/models.py`**

```python
from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Categories"

class Post(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    published = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=False)
    
    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-published']
        indexes = [
            models.Index(fields=['-published']),
        ]

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.CharField(max_length=100)
    email = models.EmailField()
    content = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Comment by {self.author} on {self.post}"
    
    class Meta:
        ordering = ['created']
```

---

### Step 4: Create Migrations

```bash
# Create migration files
python manage.py makemigrations blog

# View the migration
cat blog/migrations/0001_initial.py
```

**Output:**
```
Migrations for 'blog':
  blog/migrations/0001_initial.py
    - Create model Category
    - Create model Post
    - Create model Comment
```

---

### Step 5: Apply Migrations to Database

```bash
# Apply migrations
python manage.py migrate

# Check status
python manage.py migrate --list
```

**Output:**
```
Operations to perform:
  Apply all migrations: admin, auth, contenttypes, sessions, blog
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying auth.0001_initial... OK
  Applying auth.0002_alter_user_...  OK
  ...
  Applying blog.0001_initial... OK
```

---

### Step 6: Register Models in Admin

**Edit: `blog/admin.py`**

```python
from django.contrib import admin
from .models import Category, Post, Comment

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'category', 'is_published', 'published']
    list_filter = ['is_published', 'category', 'published']
    search_fields = ['title', 'content']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['published', 'updated']

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['author', 'post', 'approved', 'created']
    list_filter = ['approved', 'created']
    search_fields = ['author', 'email', 'content']
    actions = ['approve_comments']
    
    def approve_comments(self, request, queryset):
        queryset.update(approved=True)
```

---

### Step 7: Register App in Settings

**Edit: `myblog/settings.py`**

Find `INSTALLED_APPS` and add `'blog'`:

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'blog',  # ← Add this
]
```

---

### Step 8: Create Views

**Edit: `blog/views.py`**

```python
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from django.db.models import Q
from .models import Post, Category, Comment
from django.contrib.auth.decorators import login_required

# Function-based views
def post_list(request):
    """Display all published posts"""
    posts = Post.objects.filter(is_published=True).select_related('author', 'category')
    
    # Filter by category
    category = request.GET.get('category')
    if category:
        posts = posts.filter(category__slug=category)
    
    # Search
    search = request.GET.get('search')
    if search:
        posts = posts.filter(
            Q(title__icontains=search) | Q(content__icontains=search)
        )
    
    context = {
        'posts': posts,
        'categories': Category.objects.all(),
    }
    return render(request, 'blog/post_list.html', context)

def post_detail(request, slug):
    """Display single post with comments"""
    post = get_object_or_404(Post, slug=slug, is_published=True)
    comments = post.comments.filter(approved=True)
    
    context = {
        'post': post,
        'comments': comments,
    }
    return render(request, 'blog/post_detail.html', context)

@login_required
def add_comment(request, slug):
    """Add comment to post"""
    post = get_object_or_404(Post, slug=slug)
    
    if request.method == 'POST':
        Comment.objects.create(
            post=post,
            author=request.POST.get('author'),
            email=request.POST.get('email'),
            content=request.POST.get('content'),
        )
    
    return redirect('post_detail', slug=slug)
```

---

### Step 9: Create URL Patterns

**Create: `blog/urls.py`** (new file)

```python
from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    path('', views.post_list, name='post_list'),
    path('post/<slug:slug>/', views.post_detail, name='post_detail'),
    path('post/<slug:slug>/comment/', views.add_comment, name='add_comment'),
]
```

**Edit: `myblog/urls.py`**

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('blog/', include('blog.urls')),  # ← Add this
]
```

---

### Step 10: Create Templates

**Create: `blog/templates/blog/post_list.html`**

```html
{% extends 'base.html' %}

{% block content %}
<div class="container">
    <h1>Blog Posts</h1>
    
    <!-- Search Form -->
    <form method="get">
        <input type="text" name="search" placeholder="Search posts...">
        <button>Search</button>
    </form>
    
    <!-- Posts List -->
    <div class="posts">
        {% for post in posts %}
        <article>
            <h2><a href="{% url 'blog:post_detail' post.slug %}">{{ post.title }}</a></h2>
            <p class="meta">
                By {{ post.author.get_full_name }}
                | {{ post.published|date:"F d, Y" }}
                | {{ post.category }}
            </p>
            <p>{{ post.content|truncatewords:30 }}</p>
            <a href="{% url 'blog:post_detail' post.slug %}">Read More →</a>
        </article>
        {% empty %}
        <p>No posts found.</p>
        {% endfor %}
    </div>
</div>
{% endblock %}
```

**Create: `blog/templates/blog/post_detail.html`**

```html
{% extends 'base.html' %}

{% block content %}
<article>
    <h1>{{ post.title }}</h1>
    <p class="meta">
        By {{ post.author.get_full_name }}
        | {{ post.published|date:"F d, Y" }}
        | <a href="?category={{ post.category.slug }}">{{ post.category }}</a>
    </p>
    
    <div class="content">
        {{ post.content|linebreaks }}
    </div>
    
    <hr>
    
    <h3>Comments ({{ comments.count }})</h3>
    
    {% for comment in comments %}
    <div class="comment">
        <strong>{{ comment.author }}</strong> - {{ comment.created|date:"M d, Y" }}
        <p>{{ comment.content }}</p>
    </div>
    {% endfor %}
    
    <h3>Add Comment</h3>
    <form method="post" action="{% url 'blog:add_comment' post.slug %}">
        {% csrf_token %}
        <input type="text" name="author" placeholder="Your name" required>
        <input type="email" name="email" placeholder="Your email" required>
        <textarea name="content" placeholder="Your comment" required></textarea>
        <button>Post Comment</button>
    </form>
</article>
{% endblock %}
```

---

### Step 11: Create Superuser

```bash
python manage.py createsuperuser
```

**Prompts:**
```
Username: admin
Email: admin@example.com
Password: ****
Password (again): ****
Superuser created successfully.
```

---

### Step 12: Run Development Server

```bash
python manage.py runserver
```

**Output:**
```
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.
```

---

### Step 13: Test the Application

#### Access Admin Panel
```
URL: http://localhost:8000/admin/
Username: admin
Password: (what you entered)
```

**Create test data:**
1. Add a Category: "Technology"
2. Add a Post:
   - Title: "Django Tutorial"
   - Slug: "django-tutorial"
   - Author: admin
   - Category: Technology
   - Content: "Lorem ipsum..."
   - Published: ✓

#### View Blog
```
URL: http://localhost:8000/blog/
```

#### View Post Detail
```
URL: http://localhost:8000/blog/post/django-tutorial/
```

---

### Step 14: Database Inspection

```bash
# Open Django shell
python manage.py shell

# Query posts
>>> from blog.models import Post
>>> posts = Post.objects.all()
>>> posts.count()
1

>>> post = posts.first()
>>> post.title
'Django Tutorial'

>>> post.comments.all()
<QuerySet []>

>>> from django.contrib.auth.models import User
>>> user = User.objects.get(username='admin')
>>> user.email
'admin@example.com'

# Exit shell
>>> exit()
```

---

### Step 15: Common Tasks

#### Add More Categories
```bash
python manage.py shell
>>> from blog.models import Category
>>> Category.objects.create(name='Python', description='Python programming')
>>> Category.objects.create(name='Web Development')
```

#### Publish More Posts
```bash
python manage.py shell
>>> from blog.models import Post
>>> from django.contrib.auth.models import User
>>> author = User.objects.get(username='admin')
>>> Post.objects.create(
...     title='Python Tips',
...     slug='python-tips',
...     content='Great tips for Python developers...',
...     author=author,
...     is_published=True
... )
```

#### View All Comments
```bash
python manage.py shell
>>> from blog.models import Comment
>>> Comment.objects.filter(approved=True)
>>> Comment.objects.filter(approved=False)
```

---

### Step 16: Make Changes & Update

```bash
# Edit models.py to add a field
# Then:

python manage.py makemigrations blog
# Migration created: 0002_post_featured.py

python manage.py migrate blog
# Applied: blog.0002_post_featured

# Go to admin to see the change
```

---

### Complete Project Structure

```
myblog/
├── manage.py
├── db.sqlite3
├── myblog/
│   ├── __init__.py
│   ├── settings.py        ← Register 'blog' in INSTALLED_APPS
│   ├── urls.py            ← Include blog URLs
│   ├── asgi.py
│   └── wsgi.py
├── blog/
│   ├── migrations/
│   │   ├── __init__.py
│   │   └── 0001_initial.py
│   ├── templates/
│   │   └── blog/
│   │       ├── post_list.html
│   │       └── post_detail.html
│   ├── __init__.py
│   ├── admin.py           ← Register models
│   ├── apps.py
│   ├── models.py          ← Define Post, Comment, Category
│   ├── tests.py
│   ├── urls.py            ← Define URL patterns
│   └── views.py           ← Handle requests
└── templates/
    └── base.html          ← Base template
```

---

### Key Takeaways

| Step | Command | File |
|------|---------|------|
| 1 | `django-admin startproject` | Create project |
| 2 | `python manage.py startapp` | Create app |
| 3 | Edit `models.py` | Define database tables |
| 4 | `python manage.py makemigrations` | Create migration files |
| 5 | `python manage.py migrate` | Apply to database |
| 6 | Edit `admin.py` | Register models in admin |
| 7 | Edit `settings.py` | Add app to INSTALLED_APPS |
| 8 | Edit `views.py` | Create logic |
| 9 | Create `urls.py` | Define URL patterns |
| 10 | Create templates | Create HTML |
| 11 | `python manage.py createsuperuser` | Create admin user |
| 12 | `python manage.py runserver` | Run development server |

