from itertools import count

from django.core.validators import MinValueValidator
from django.db import models


import actions
from scheduler import utils


DEFAULT_PRIORITY = 10


class ScheduleEntry(models.Model):
    """Describes a series of scheduler tasks.

    An schedule entry is at minimum a human readable name and an associated
    action. Combining different values of `start`, `stop`, `interval`, and
    `priority` allows for flexible task scheduling. If no start time is given,
    the scheduler begins scheduling tasks immediately. If no stop time is
    given, the scheduler continues scheduling tasks until the schedule entry's
    :attr:`canceled` flag is set. If no interval is given, the scheduler will
    schedule exactly one task and then set :attr:`canceled`. `interval=None`
    can be used with either an immediate or future start time. If two tasks are
    scheduled to run at the same time, they will be run in order of `priority`.
    If two tasks are scheduled to run at the same time and have the same
    `priority`, execution order is undefined.

    """

    # Implementation notes:
    #
    # Large series of tasks are possible due to the "laziness" of the internal
    # `range`-based representation of task times:
    #
    #     >>> sys.getsizeof(range(1, 2))
    #     48
    #     >>> sys.getsizeof(range(1, 20000000000000))
    #     48
    #
    # `take_until` consumes times up to `t` from the internal range by moving
    # `next_task_time` forward in time and returning a `range` representing the
    # taken time slice. No other methods or properties actually consume times.
    #
    #     >>> entry = ScheduleEntry(name='test', start=5, stop=10, interval=1,
    #     ...                       action='logger')
    #     >>> list(entry.take_until(7))
    #     [5, 6]
    #     >>> list(entry.get_remaining_times())
    #     [7, 8, 9]
    #     >>> entry.take_until(9)
    #     range(7, 9)
    #     >>> list(_)
    #     [7, 8]
    #
    # When `stop` is `None`, the schedule entry replaces `range` with
    # `itertools.count`. A `count` provides an interface compatible with a
    # range iterator, but it's best not to do something like
    # `list(e.get_remaining_times())` from the example above on one.

    def timefn():
        """Make `start` time default to upcoming second."""
        return utils.timefn()

    name = models.SlugField(primary_key=True)
    action = models.CharField(choices=actions.CHOICES,
                              max_length=actions.MAX_LENGTH)
    priority = models.SmallIntegerField(default=DEFAULT_PRIORITY)
    start = models.BigIntegerField(default=timefn, blank=True)
    stop = models.BigIntegerField(default=None, null=True, blank=True)
    relative_stop = models.BooleanField(default=False)
    interval = models.PositiveIntegerField(default=None, null=True, blank=True,
                                           validators=(MinValueValidator(1),))
    canceled = models.BooleanField(default=False, editable=True)
    next_task_time = models.BigIntegerField(default=timefn, editable=False)
    next_task_id = models.IntegerField(default=1, editable=False)

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'schedule'
        ordering = ('created',)

    def __init__(self, *args, **kwargs):
        super(ScheduleEntry, self).__init__(*args, **kwargs)
        self._make_relative_stop_absolute()

    def _make_relative_stop_absolute(self):
        """After model fields are initialized, ensure `stop` is absolute."""
        if self.relative_stop:
            self.stop = self.start + self.stop
            self.relative_stop = False

    def take_pending(self):
        """Take the range of times up to and including now."""
        now = utils.timefn()
        return self.take_until(now)

    def take_until(self, t=None):
        """Take the range of times before `t`.

        :param t: a :func:`timefn` timestamp

        """
        times = self.get_remaining_times(until=t)
        if times:
            if self.interval:
                self.next_task_time = times[-1] + self.interval
            else:
                # interval is None and time consumed
                self.canceled = True

        return times

    def has_remaining_times(self):
        """Return :obj:`True` if task times remain, else :obj:`False`."""
        return self.next_task_time in self.get_remaining_times()

    def get_remaining_times(self, until=None):
        """Get a potentially infinite iterator of remaining task times."""
        if self.canceled:
            return range(0)

        next_time = self.next_task_time
        stop = self.stop

        if until is None and stop is None:
            if self.interval:
                return count(next_time, self.interval)         # infinite
            else:
                return iter(range(next_time, next_time + 1))   # one-shot

        stop = min(t for t in (until, stop) if t is not None)

        interval = self.interval or abs(stop - next_time)
        times = range(next_time, stop, interval)
        return times

    def get_next_task_id(self):
        next_task_id = self.next_task_id
        self.next_task_id += 1
        return next_task_id

    def __str__(self):
        fmtstr = 'name={}, pri={}, start={}, stop={}, ival={}, action={}>'
        return fmtstr.format(
            self.name,
            self.priority,
            self.start,
            ('+' * self.relative_stop + '{}').format(self.stop),
            self.interval,
            self.action
        )