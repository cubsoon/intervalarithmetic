set_rounding = None
get_rounding = None

TO_ZERO = None
TOWARD_MINUS_INF = None
TOWARD_MINUS_INF = None
TO_NEAREST = None

def _start_libm():
    global TO_ZERO, TOWARD_MINUS_INF, TOWARD_PLUS_INF, TO_NEAREST
    global set_rounding, get_rounding
    from ctypes import cdll
    from ctypes.util import find_library
    libm = cdll.LoadLibrary(find_library('m'))
    set_rounding, get_rounding = libm.fesetround, libm.fegetround
    # x86
    TO_ZERO = 0xc00
    TOWARD_MINUS_INF = 0x400
    TOWARD_PLUS_INF = 0x800
    TO_NEAREST = 0

def _start_msvcrt():
    global TO_ZERO, TOWARD_MINUS_INF, TOWARD_PLUS_INF, TO_NEAREST
    global set_rounding, get_rounding
    from ctypes import cdll
    msvcrt = cdll.msvcrt
    set_rounding = lambda mode: msvcrt._controlfp(mode, 0x300)
    get_rounding = lambda: msvcrt._controlfp(0, 0)
    TO_ZERO = 0x300
    TOWARD_MINUS_INF = 0x100
    TOWARD_PLUS_INF = 0x200
    TO_NEAREST = 0

for _start_rounding in _start_libm, _start_msvcrt:
    try:
        _start_rounding()
        break
    except:
        pass
else:
    raise RuntimeError("Could not start FPU mode change module.")

class Interval:
    """
    Class of objects representing real numbers as intervals between two machine numbers.
    """

    def __init__(self, left=None, right=None, value=None, strict=False):
        # default rounding (not using while creating interval)
        # use decimal as exact value holder
        from decimal import Decimal
        from numpy import nextafter

        self.strict = strict

        if value and (not left) and (not right):
            exact = Decimal(value)
            float_repr = Decimal("{0:0.70f}".format(float(exact)))
            if exact == float_repr:
                self.lv = float(float_repr)
                self.rv = float(float_repr)
            elif exact > float_repr:
                self.lv = float(float_repr)
                self.rv = nextafter(self.lv, float('Inf'))
            elif exact < float_repr:
                self.rv = float(float_repr)
                self.lv = nextafter(self.rv, -float('Inf'))
        elif (not value) and left and right:
            exact_left = Decimal(left)
            exact_right = Decimal(right)
            if exact_left > exact_right:
                raise ValueError("Left edge greater than right.")
            float_repr_left = Decimal(float(exact_left))
            float_repr_right = Decimal(float(exact_right))
            if exact_left < float_repr_left:
                self.lv = nextafter(float(float_repr_left), -float('Inf'))
            else:
                self.lv = float(float_repr_left)
            if exact_right > float_repr_right:
                self.rv = nextafter(float(float_repr_right), float('Inf'))
            else:
                self.rv = float(float_repr_right)
        elif (not value) and (not left) and (not right):
            self.lv = 0.0
            self.rv = 0.0
        else:
            raise ValueError("Wrong arguments passed while creating interval.")

    def _process_other(self, other):
        if isinstance(other, Interval):
            return other
        elif not self.strict:
            try:
                return Interval(value=other, strict=self.strict)
            except:
                raise ValueError("Can't use other value from overloaded operator as numeric.")
        else:
            raise ValueError("Can't use overloaded operator with non-interval in strict mode.")

    def __add__(self, other):
        return Interval.iadd(self, self._process_other(other))

    def __radd__(self, other):
        return Interval.iadd(self._process_other(other), self)

    def __sub__(self, other):
        return Interval.isubtract(self, self._process_other(other))

    def __rsub__(self, other):
        return Interval.isubtract(self._process_other(other), self)

    def __mul__(self, other):
        return Interval.imultiply(self, self._process_other(other))

    def __rmul__(self, other):
        return Interval.imultiply(self._process_other(other), self)

    def __truediv__(self, other):
        return Interval.idivide(self, self._process_other(other))

    def __rtruediv__(self, other):
        return Interval.idivide(self._process_other(other), self)

    def __float__(self):
        return self.lv + Interval.iwidth(self)/2

    @staticmethod
    def iwidth(interval):
        assert isinstance(interval, Interval)
        set_rounding(TOWARD_PLUS_INF)
        ret = interval.rv - interval.lv
        set_rounding(TO_NEAREST)
        return ret

    @staticmethod
    def iadd(lint, rint):
        assert isinstance(lint, Interval)
        assert isinstance(rint, Interval)
        ret = Interval()
        set_rounding(TOWARD_MINUS_INF)
        ret.lv = lint.lv + rint.lv
        set_rounding(TOWARD_PLUS_INF)
        ret.rv = lint.rv + rint.rv
        set_rounding(TO_NEAREST)
        ret.strict = lint.strict or rint.strict
        return ret

    @staticmethod
    def isubtract(lint, rint):
        assert isinstance(lint, Interval)
        assert isinstance(rint, Interval)
        ret = Interval()
        set_rounding(TOWARD_MINUS_INF)
        ret.lv = lint.lv - rint.rv
        set_rounding(TOWARD_PLUS_INF)
        ret.rv = lint.rv - rint.lv
        set_rounding(TO_NEAREST)
        ret.strict = lint.strict or rint.strict
        return ret

    @staticmethod
    def imultiply(lint, rint):
        assert isinstance(lint, Interval)
        assert isinstance(rint, Interval)
        ret = Interval()
        set_rounding(TOWARD_MINUS_INF)
        ret.lv = min(lint.lv*rint.lv, lint.lv*rint.rv, lint.rv*rint.lv, lint.rv*rint.rv)
        set_rounding(TOWARD_PLUS_INF)
        ret.rv = max(lint.lv*rint.lv, lint.lv*rint.rv, lint.rv*rint.lv, lint.rv*rint.rv)
        set_rounding(TO_NEAREST)
        ret.strict = lint.strict or rint.strict
        return ret

    @staticmethod
    def idivide(lint, rint):
        assert isinstance(lint, Interval)
        assert isinstance(rint, Interval)
        if rint.lv <= 0.0 <= rint.rv:
            raise ZeroDivisionError("Division by an interval containing 0.")
        ret = Interval()
        set_rounding(TOWARD_MINUS_INF)
        ret.lv = min(lint.lv/rint.lv, lint.lv/rint.rv, lint.rv/rint.lv, lint.rv/rint.rv)
        set_rounding(TOWARD_PLUS_INF)
        ret.rv = max(lint.lv/rint.lv, lint.lv/rint.rv, lint.rv/rint.lv, lint.rv/rint.rv)
        set_rounding(TO_NEAREST)
        ret.strict = lint.strict or rint.strict
        return ret

    @staticmethod
    def ipi(strict=False):
        return Interval(value='3.1415926535897932384626433832795028841972', strict=strict)

    @staticmethod
    def ie(strict=False):
        return Interval(value='2.7182818284590452353602874713526624977572', strict=strict)

    @staticmethod
    def izero(strict=False):
        return Interval(value='0', strict=strict)

    @staticmethod
    def ione(strict=False):
        return Interval(value='1', strict=strict)

    def __str__(self):
        return "<{0:0.20f}; {1:0.20f}>".format(self.lv, self.rv)

    def __repr__(self):
        return self.__str__()