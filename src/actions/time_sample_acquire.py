"""Take an acquisition."""

from __future__ import absolute_import

import logging
from itertools import compress

import numpy as np

from rest_framework.reverse import reverse
from sigmf.sigmffile import SigMFFile

from capabilities.models import SensorDefinition
from capabilities.serializers import SensorDefinitionSerializer
from sensor import V1, settings, utils

from .base import Action
from . import usrp


logger = logging.getLogger(__name__)


GLOBAL_INFO = {
    "core:datatype": "f32_le",  # 32-bit float, Little Endian
    "core:version": "0.0.1"
}



# FIXME: this needs to be defined globally somewhere
SCOS_TRANSFER_SPEC_VER = '0.1'


class SingleTimeAcquisition(Action):
    """ Collect a sample of data

    :param frequency: center frequency in Hz
    :param sample_rate: requested sample_rate in Hz
    :param num_samples: number of samples to collect
    """
    def __init__(self, frequency, sample_rate,num_samples):
        super(SingleTimeAcquisition, self).__init__()

        self.frequency = frequency
        self.sample_rate = sample_rate
        self.num_samples = num_samples
        self.usrp = usrp  # make instance variable to allow hotswapping mock
        self.enbw = None

    def __call__(self, schedule_entry_name, task_id):
        from schedule.models import ScheduleEntry

        # raises ScheduleEntry.DoesNotExist if no matching schedule entry
        parent_entry = ScheduleEntry.objects.get(name=schedule_entry_name)

        # check to see if USRP is available
        self.test_required_components()

        # set sample rate, frequency
        self.configure_usrp()

        # acquire the data from the sensor
        data = self.acquire_data(parent_entry, task_id)

        # create the signal model
        sigmf_md = self.build_sigmf_md()

        # store the signal in the database
        self.archive(data, sigmf_md, parent_entry, task_id)

        # update the web app
        kws = {'schedule_entry_name': schedule_entry_name, 'task_id': task_id}
        kws.update(V1)
        detail = reverse(
            'acquisition-detail',
            kwargs=kws,
            request=parent_entry.request
        )

        return detail

    def test_required_components(self):
        """Fail acquisition if a required component is not available."""
        if not self.usrp.is_available:
            self.usrp.connect()

        # set any components that must be found in this list
        required_components = (
            self.usrp.is_available,
        )
        component_names = ("UHD", "USRP")
        missing_components = [not rc for rc in required_components]
        if any(missing_components):
            missing = tuple(compress(component_names, missing_components))
            msg = "acquisition failed: {} required but not available"
            raise RuntimeError(msg.format(missing))

    def configure_usrp(self):
        self.set_usrp_clock_rate()
        self.set_usrp_sample_rate()
        self.set_usrp_frequency()

    def set_usrp_sample_rate(self):
        self.usrp.radio.sample_rate = self.sample_rate
        self.sample_rate = self.usrp.radio.sample_rate

    def set_usrp_clock_rate(self):
        clock_rate = self.sample_rate
        while clock_rate < 10e6:
            clock_rate *= 4

        self.usrp.radio.clock_rate = clock_rate

    def set_usrp_frequency(self):
        requested_frequency = self.frequency
        self.usrp.radio.frequency = requested_frequency
        self.frequency = self.usrp.radio.frequency

    def acquire_data(self, parent_entry, task_id):
        msg = "Acquiring {} points at {} MHz"
        logger.debug(msg.format(self.num_samples, self.frequency / 1e6))

        data = self.usrp.radio.acquire_samples(self.num_samples)
        #data.resize((self.nffts, self.fft_size))

        return data

    def build_sigmf_md(self):
        logger.debug("Building SigMF metadata file")

        sigmf_md = SigMFFile()
        sigmf_md.set_global_field("core:datatype", "rf32_le")
        sigmf_md.set_global_field("core:sample_rate", self.sample_rate)
        sigmf_md.set_global_field("core:description", self.description)

        sensor_def_obj = SensorDefinition.objects.get()
        sensor_def_json = SensorDefinitionSerializer(sensor_def_obj).data
        sigmf_md.set_global_field("scos:sensor_definition", sensor_def_json)

        try:
            fqdn = settings.ALLOWED_HOSTS[1]
        except IndexError:
            fqdn = 'not.set'

        sigmf_md.set_global_field("scos:sensor_id", fqdn)
        sigmf_md.set_global_field("scos:version", SCOS_TRANSFER_SPEC_VER)

        capture_md = {
            "core:frequency": self.frequency,
            "core:time": utils.get_datetime_str_now()
        }

        sigmf_md.add_capture(start_index=0, metadata=capture_md)

        # for i, detector in enumerate(M4sDetector):
        #     single_frequency_fft_md = {
        #         "number_of_samples_in_fft": self.fft_size,
        #         "window": "blackman",
        #         "equivalent_noise_bandwidth": self.enbw,
        #         "detector": detector.name + "_power",
        #         "number_of_ffts": self.nffts,
        #         "units": "dBm",
        #         "reference": "not referenced"
        #     }

        #     annotation_md = {
        #         "scos:measurement_type": {
        #             "single_frequency_fft_detection": single_frequency_fft_md,
        #         }
        #     }

        #     sigmf_md.add_annotation(
        #         start_index=(i * self.fft_size),
        #         length=self.fft_size,
        #         metadata=annotation_md
        #     )

        return sigmf_md

    def archive(self, m4s_data, sigmf_md, parent_entry, task_id):
        from acquisitions.models import Acquisition

        logger.debug("Storing acquisition in database")

        Acquisition(
            schedule_entry=parent_entry,
            task_id=task_id,
            sigmf_metadata=sigmf_md._metadata,
            data=m4s_data
        ).save()

    @property
    def description(self):
        return """Collect {} samples at {:.2f} MHz.

        The radio will use a sample rate of {:.2f} MHz.

        """.format(
            self.num_samples,
            self.frequency / 1e6,
            self.sample_rate / 1e6
        )
