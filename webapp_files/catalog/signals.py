import json

from django.core.serializers.json import DjangoJSONEncoder
from django.db.models.signals import m2m_changed, post_save, pre_delete, pre_save
from django.dispatch import receiver

from .audit import get_current_actor
from .models import (
    AuditEvent,
    Comment,
    Location,
    Route,
    RouteWaypoint,
    User,
    Waypoint,
)

EXCLUDED_FIELDS = {"password", "last_login"}
AUDITED_MANY_TO_MANY = {
    User: ("prev_routes", "saved_routes", "marked_locations"),
    Route: ("marked_locations",),
    Waypoint: ("routes",),
}


def _snapshot(instance):
    values = {}
    for field in instance._meta.concrete_fields:
        if field.primary_key or field.name in EXCLUDED_FIELDS:
            continue
        value = field.value_from_object(instance)
        values[field.name] = json.loads(json.dumps(value, cls=DjangoJSONEncoder))
    return values


def _record(instance, action, changes):
    actor = get_current_actor()
    AuditEvent.objects.create(
        action=action,
        actor_user_id=actor[0] if actor else "",
        actor_username=actor[1] if actor else "",
        object_type=instance._meta.label,
        object_id=str(instance.pk),
        object_label=str(instance)[:255],
        changes=changes,
    )


@receiver(pre_save, sender=User)
@receiver(pre_save, sender=Location)
@receiver(pre_save, sender=Route)
@receiver(pre_save, sender=Waypoint)
@receiver(pre_save, sender=RouteWaypoint)
@receiver(pre_save, sender=Comment)
def capture_previous_values(sender, instance, **kwargs):
    if instance.pk is None:
        instance._audit_previous_values = None
        return

    previous = sender._base_manager.filter(pk=instance.pk).first()
    instance._audit_previous_values = _snapshot(previous) if previous else None


@receiver(post_save, sender=User)
@receiver(post_save, sender=Location)
@receiver(post_save, sender=Route)
@receiver(post_save, sender=Waypoint)
@receiver(post_save, sender=RouteWaypoint)
@receiver(post_save, sender=Comment)
def record_saved_object(sender, instance, created, **kwargs):
    current = _snapshot(sender._base_manager.get(pk=instance.pk))
    previous = getattr(instance, "_audit_previous_values", None)

    if created or previous is None:
        changes = {name: {"old": None, "new": value} for name, value in current.items()}
        action = AuditEvent.Action.CREATE
    else:
        changes = {
            name: {"old": previous[name], "new": value}
            for name, value in current.items()
            if previous.get(name) != value
        }
        if not changes:
            return
        action = AuditEvent.Action.UPDATE

    _record(instance, action, changes)


@receiver(pre_delete, sender=User)
@receiver(pre_delete, sender=Location)
@receiver(pre_delete, sender=Route)
@receiver(pre_delete, sender=Waypoint)
@receiver(pre_delete, sender=RouteWaypoint)
@receiver(pre_delete, sender=Comment)
def record_deleted_object(sender, instance, **kwargs):
    changes = {
        name: {"old": value, "new": None} for name, value in _snapshot(instance).items()
    }
    _record(instance, AuditEvent.Action.DELETE, changes)


@receiver(m2m_changed)
def record_many_to_many_change(sender, instance, action, reverse, **kwargs):
    for model, field_names in AUDITED_MANY_TO_MANY.items():
        if not any(
            model._meta.get_field(name).remote_field.through is sender
            for name in field_names
        ):
            continue

        for field_name in field_names:
            field = model._meta.get_field(field_name)
            if field.remote_field.through is not sender:
                continue
            expected_model = field.remote_field.model if reverse else model
            if not isinstance(instance, expected_model):
                continue

            relation_name = (
                field.remote_field.get_accessor_name() if reverse else field_name
            )
            manager = getattr(instance, relation_name)
            key = (sender, field_name, reverse)
            snapshots = getattr(instance, "_audit_m2m_snapshots", {})

            if action.startswith("pre_"):
                snapshots[key] = sorted(manager.values_list("pk", flat=True))
                instance._audit_m2m_snapshots = snapshots
                return

            if not action.startswith("post_"):
                return
            previous = snapshots.pop(key, [])
            current = sorted(manager.values_list("pk", flat=True))
            if previous != current:
                _record(
                    instance,
                    AuditEvent.Action.UPDATE,
                    {
                        relation_name: {
                            "old": previous,
                            "new": current,
                        }
                    },
                )
            return
