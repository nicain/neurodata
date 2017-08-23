import numpy as np

SEC = SECOND = 'second'
MS = MILLISECOND = 'millisecond'
NONE = NONDIMENSIONAL = 'nondimensional'
temporal_conversion_dict = {MS:.001, SEC:1., NONE:None}
TIME_UNIT_LIST = [MS, SEC, NONE]

class TemporalData(object):
    
    sort_mode = 'start'
    
    def __init__(self, unit):        
        self._master = None
        self._unit = unit

    @property
    def unit(self):
        return self._unit

    @property
    def master(self):
        return self._master

    @property
    def is_master(self):
        return self.master is self

    def set_as_master(self):
        self._master = self

    def set_master_timeline(self, other_TimeSeries):
        
        # Set the other timeline to be its own master, if note done already:
        if other_TimeSeries.master is None:
            other_TimeSeries.set_as_master()

        # Ensure that the other timeline is a master timeline
        if not other_TimeSeries.is_master:
            raise Exception 

        # Slave current timeline to master:
        self._master = other_TimeSeries

    def __lt__(self, other):
        
        self_unit_convert = float(temporal_conversion_dict[self.unit])
        other_unit_convert = float(temporal_conversion_dict[other.unit])

        if TemporalData.sort_mode == 'start':
            self_test = self[0]
            other_test = other[0]
        elif TemporalData.sort_mode == 'end':
            self_test = self[-1]
            other_test = other[-1]
        elif TemporalData.sort_mode == 'duration':
            self_test = self.duration
            other_test = other.duration
        elif TemporalData.sort_mode == 'middle':
            self_test = float((self[-1] + self[0]))/2
            other_test = float((other[-1] + other[0]))/2
        else:
            raise NotImplementedError
        other_test *= (other_unit_convert/self_unit_convert)
       
        if self_test == other_test:
            return self.duration < other.duration
        else:
            return self_test < other_test

    def __gt__(self, other):
        return other.__lt__(self)

    @staticmethod
    def sort(input_list, how='start', **kwargs):
        old_how = TemporalData.sort_mode
        TemporalData.sort_mode = how
        output_list = sorted(input_list, **kwargs)
        TemporalData.sort_mode = old_how
        return output_list

class TimeEvent(TemporalData):
    
    def __init__(self, t, unit):
        
        super(TimeEvent, self).__init__(unit)
        


        self._t = t
        self._unit = unit

    @property
    def is_master(self):
        return False

    @property
    def t(self):
        return self._t

    @property
    def set_as_master(self):
        raise RuntimeError("%s cannot be master" % self.__class__)

    def set_master_timeline(self, other_TimeSeries, offset, offset_unit):
        assert offset_unit in TIME_UNIT_LIST
        
        super(TimeEvent, self).set_master_timeline(other_TimeSeries)

        # Shift current timeline back to master:
        curr_unit_convert = float(temporal_conversion_dict[self.unit])
        offset_unit_convert = float(temporal_conversion_dict[offset_unit])
        self._t -= offset*(offset_unit_convert/curr_unit_convert)

        # Scale current timeline consistent with master:
        master_unit_convert = float(temporal_conversion_dict[self.master.unit])
        self._t /= (master_unit_convert/curr_unit_convert)

        # Set current unit consistent with master:
        self._unit = self.master.unit

class TimestampTimeSeries(TemporalData):

    def __init__(self, timestamps, unit):
        assert unit in TIME_UNIT_LIST
        super(TimestampTimeSeries, self).__init__(unit)

    
        self._timestamps = np.array(timestamps, dtype=np.float)

    def __getitem__(self, ii):
        return self._timestamps[ii]

    @property
    def timestamps(self):
        return self._timestamps

    @property
    def duration(self):
        self.stop - self.start 

    @property
    def stop(self):
        return self.timestamps[-1]

    @property
    def start(self):
        return self.timestamps[0]

    def __len__(self):
        return len(self.timestamps)

    def set_master_timeline(self, other_TimeSeries, offset, offset_unit):
        assert offset_unit in TIME_UNIT_LIST
        
        super(TimestampTimeSeries, self).set_master_timeline(other_TimeSeries)

        # Shift current timeline back to master:
        curr_unit_convert = float(temporal_conversion_dict[self.unit])
        offset_unit_convert = float(temporal_conversion_dict[offset_unit])
        self._timestamps -= offset*(offset_unit_convert/curr_unit_convert)

        # Scale current timeline consistent with master:
        master_unit_convert = float(temporal_conversion_dict[self.master.unit])
        self._timestamps /= (master_unit_convert/curr_unit_convert)

        # Set current unit consistent with master:
        self._unit = self.master.unit

class PeriodicTimeSeries(TemporalData):
    
    def __init__(self, start, rate, unit):
        assert unit in TIME_UNIT_LIST
        super(PeriodicTimeSeries, self).__init__(unit)

        self._start = start
        self._rate = rate

    @property
    def start(self):
        return self._start

    @property
    def duration(self):
        return np.inf

    def __getitem__(self, ii):
        
        if isinstance(ii, slice):
            assert not ii.stop is None

            if ii.step is None and not ii.start is None:
                curr_array = np.array([x for x in range(ii.start, ii.stop)])
            elif ii.step is None and ii.start is None:
                curr_array = np.array([x for x in range(0, ii.stop)])
            else:
                curr_array = np.array([x for x in range(ii.start, ii.step, ii.stop)])
            
            return self._shift_and_scale(curr_array)
        else:
            return self._shift_and_scale(ii)


    def _shift_and_scale(self, x):
        return (self._start + self._rate*x)
         

    def set_master_timeline(self, other_TimeSeries, offset, offset_unit):
        assert offset_unit in TIME_UNIT_LIST
        
        super(PeriodicTimeSeries, self).set_master_timeline(other_TimeSeries)

        # Shift current timeline back to master:
        curr_unit_convert = float(temporal_conversion_dict[self.unit])
        offset_unit_convert = float(temporal_conversion_dict[offset_unit])
        self._start -= offset*(offset_unit_convert/curr_unit_convert)

        # Scale current timeline consistent with master:
        master_unit_convert = float(temporal_conversion_dict[self.master.unit])
        self._start /= (master_unit_convert/curr_unit_convert)
        self._rate /= (master_unit_convert/curr_unit_convert)

        # Set current unit consistent with master:
        self._unit = self.master.unit

class StartStopEpoch(TimestampTimeSeries):
    
    def __init__(self, start, stop, unit):
        
        super(StartStopEpoch, self).__init__((start, stop), unit)

    @property
    def start(self):
        return self[0]

    @property
    def stop(self):
        return self[1]

    @property
    def duration(self):
        return self.stop-self.start

    @property
    def set_as_master(self):
        raise RuntimeError("%s cannot be master" % self.__class__)

class DurationEpoch(StartStopEpoch):
    def __init__(self, start, duration, unit):
        super(StartStopEpoch, self).__init__((start, start+duration), unit)



if __name__ == "__main__":

    # Example 1:
    # ts = TimestampTimeSeries(np.arange(200), MS)
    # mts = PeriodicTimeSeries(.01, .001, SEC)
    # print mts[:5], mts.master
    # mts.set_master_timeline(ts, 1, MS)
    # print mts[:5], mts.master, mts.unit


    # Example 2:
    # mts = TimestampTimeSeries(10+np.arange(200), MS)
    # ts = PeriodicTimeSeries(.005, .001, SEC)
    # print mts[:5]
    # mts.set_master_timeline(ts, 1, MS)
    # print mts[:5]

    # ts = PeriodicTimeSeries(.005, .001, SEC)
    # tmp = TimeEvent(10, MS)
    # print tmp.t
    # tmp.set_master_timeline(ts, 1, MS)
    # print tmp.t


    # ts = PeriodicTimeSeries(.005, .001, SEC)
    # tmp = StartStopEpoch(10,20,MS)
    # print tmp.start, tmp.stop, tmp.duration
    # tmp.set_master_timeline(ts, 1, MS)
    # print tmp.start, tmp.stop, tmp.duration

    # ts = PeriodicTimeSeries(.005, .001, SEC)
    # tmp = DurationEpoch(10,5,MS)
    # print tmp.start, tmp.stop, tmp.duration
    # tmp.set_master_timeline(ts, 1, MS)
    # print tmp.start, tmp.stop, tmp.duration

    a = DurationEpoch(10,25,MS)
    b = DurationEpoch(10,24,MS)
    c = DurationEpoch(20,2,MS)
    for e in TemporalData.sort([c,b,a]):
        print e.start, e.stop, e.duration
    print
    for e in TemporalData.sort([a,b,c], how='end'):
        print e.start, e.stop,  e.duration
    print
    for e in TemporalData.sort([a,b,c], how='duration'):
        print e.start, e.stop,  e.duration
    print
    for e in TemporalData.sort([a,b,c], how='duration', reverse=True):
        print e.start, e.stop,  e.duration
