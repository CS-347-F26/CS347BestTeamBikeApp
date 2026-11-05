from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse

# Models follow the team whiteboard (bookkeeping/images/DataModel.jpeg).
# Every model gets Django's automatic integer `id` primary key, which covers
# the "id, unique" fields on the board.


class User(AbstractUser):
    """A rider account. Extends Django's built-in user so username/password
    (hashed), login and the admin all work out of the box."""

    # Fields (username and password are inherited from AbstractUser)
    comfortability = models.PositiveSmallIntegerField(
        default=0, help_text='How comfortable this rider is on busier roads'
    )
    prev_routes = models.ManyToManyField(
        'Route', blank=True, related_name='previous_riders'
    )
    saved_routes = models.ManyToManyField(
        'Route', blank=True, related_name='saved_by'
    )
    marked_locations = models.ManyToManyField(
        'Location', blank=True, related_name='marked_by'
    )

    def __str__(self):
        """String for representing the User object (in Admin site etc.)."""
        return self.username


class Location(models.Model):
    """A point on the map, such as a stop or transfer point.
    Comments on a location are available as `location.comments`."""

    # Fields
    name = models.CharField(max_length=100)
    latitude = models.FloatField()
    longitude = models.FloatField()

    # Metadata
    class Meta:
        ordering = ['name']

    # Methods
    def __str__(self):
        """String for representing the Location object (in Admin site etc.)."""
        return self.name


class Route(models.Model):
    """A color-coded bike line, like a transit line (e.g. 'Red Line').
    Comments on a route are available as `route.comments`."""

    # Fields
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=30)
    # PROTECT stops a location from being deleted while a route still uses it.
    start_location = models.ForeignKey(
        Location, on_delete=models.PROTECT, related_name='routes_starting_here'
    )
    end_location = models.ForeignKey(
        Location, on_delete=models.PROTECT, related_name='routes_ending_here'
    )
    marked_locations = models.ManyToManyField(
        Location, blank=True, related_name='routes'
    )
    up_votes = models.PositiveIntegerField(default=0)
    down_votes = models.PositiveIntegerField(default=0)
    comfortability = models.PositiveSmallIntegerField(default=0)

    # Metadata
    class Meta:
        ordering = ['name']

    # Methods
    def get_absolute_url(self):
        """Returns the URL to access a particular route."""
        return reverse('route-detail', args=[str(self.id)])

    def __str__(self):
        """String for representing the Route object (in Admin site etc.)."""
        return self.name


class Comment(models.Model):
    """Feedback left by a user on a route or a location."""

    # Fields
    text = models.TextField()
    # Django stores this as `user_id` in the database (the board's user_id).
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    route = models.ForeignKey(
        Route, on_delete=models.CASCADE, null=True, blank=True,
        related_name='comments'
    )
    location = models.ForeignKey(
        Location, on_delete=models.CASCADE, null=True, blank=True,
        related_name='comments'
    )
    up_votes = models.PositiveIntegerField(default=0)
    down_votes = models.PositiveIntegerField(default=0)

    # Metadata
    class Meta:
        ordering = ['-id']

    # Methods
    def __str__(self):
        """String for representing the Comment object (in Admin site etc.)."""
        return self.text[:50]


class RouteFeedback(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='route_feedback',
    )
    route = models.ForeignKey(
        Route,
        on_delete=models.CASCADE,
        related_name='feedback',
    )
    comfort_rating = models.PositiveSmallIntegerField()
    text = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.route} feedback by {self.user}'