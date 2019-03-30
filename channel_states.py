class ChannelStates(dict):
    __slots__ = ()  # http://book.pythontips.com/en/latest/__slots__magic.html

    def get_state(self, sn, index):
        try:
            # return self.default_output_state_types.get(str(sn)).get(str(index))
            return self.__getitem__(str(sn)).get(str(index))
        except Exception:
            return None

    def set_state(self, sn, index, state):
        sn = str(sn)
        if sn not in self:
            self[sn] = {}
        self[sn][str(index)] = state

    def set_state2(self, ch, state):
        sn = str(ch.getDeviceSerialNumber())
        if sn not in self:
            self[sn] = {}
        self[sn][str(ch.getChannel())] = state

    def del_state(self, sn, index):
        try:
            del self[str(sn)][str(index)]
        except Exception:
            return None

    def del_sn(self, sn):
        try:
            del self[str(sn)]
        except Exception:
            return None

    #def __contains__(self, k):
    #    return super().__contains__(ensure_lower(k))
