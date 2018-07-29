from . import acquire_single_freq_fft
from . import time_sample_acquire
from . import logger
from . import monitor_usrp


# Actions initialized here are made available through the API
registered_actions = {
    "acquire700c": acquire_single_freq_fft.SingleFrequencyFftAcquisition(
        frequency=751e6,
        sample_rate=15.36e6,
        fft_size=1024,
        nffts=300
    ),
    "acquire1024samples" : time_sample_acquire.SingleTimeAcquisition(
        frequency=2.4e9,
        sample_rate=1e6,
        num_samples=1024
    ),
    "logger": logger.Logger(),
    "admin_logger": logger.Logger(loglvl=logger.LOGLVL_ERROR, admin_only=True),
    "monitor_usrp": monitor_usrp.USRPMonitor(admin_only=True)
}


by_name = registered_actions


def get_action_with_summary(action):
    action_fn = registered_actions[action]
    summary = get_summary(action_fn)
    action_with_summary = action
    if summary:
        action_with_summary += " - {}".format(summary)

    return action_with_summary


def get_summary(action_fn):
    """Extract the first line of the action's description as a summary."""
    description = action_fn.description
    summary = None
    if description:
        summary = description.splitlines()[0]

    return summary


MAX_LENGTH = 50
VALID_ACTIONS = []
CHOICES = []
ADMIN_CHOICES = []


def init():
    """Allows re-initing VALID_ACTIONS if `registered_actions` is modified."""
    global VALID_ACTIONS
    global CHOICES

    VALID_ACTIONS = sorted(registered_actions.keys())
    for action in VALID_ACTIONS:
        if registered_actions[action].admin_only:
            ADMIN_CHOICES.append((action, get_action_with_summary(action)))
        else:
            CHOICES.append((action, get_action_with_summary(action)))


init()
