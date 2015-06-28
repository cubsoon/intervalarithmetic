# Setting float rounding mode.
# ----------------------------
#   Based on:
#   https://rafaelbarreto.wordpress.com/2009/03/30/controlling-fpu-rounding-modes-with-python/

set_rounding = None
get_rounding = None

TO_ZERO = None
TOWARD_MINUS_INF = None
TOWARD_PLUS_INF = None
TO_NEAREST = None

def _init_libm():
    """
    Load glibc libm (fenv.h) rounding mode control functions.
    """
    global TO_ZERO, TOWARD_MINUS_INF, TOWARD_PLUS_INF, TO_NEAREST
    global set_rounding, get_rounding
    from ctypes import cdll
    from ctypes.util import find_library
    libm = cdll.LoadLibrary(find_library('m'))
    assert libm.fegetround
    assert libm.fesetround
    get_rounding = lambda: libm.fegetround()
    set_rounding = lambda mode: True if libm.fesetround(mode) == 0 else False
    # Macros from fenv.h are architecture dependant.
    import struct
    bit = 8 * struct.calcsize("P")
    assert bit in (32, 64)
    if bit == 32:
        # x86:
        TO_ZERO, TOWARD_PLUS_INF, TOWARD_MINUS_INF, TO_NEAREST = 0x0c00, 0x0800, 0x0400, 0x0000
        # FE_TOWARDZERO, FE_UPWARD, FE_DOWNWARD, FE_TONEAREST
    else:
        # ia64:
        TO_ZERO, TOWARD_PLUS_INF, TOWARD_MINUS_INF, TO_NEAREST = 3, 2, 1, 0
        # FE_TOWARDZERO, FE_UPWARD, FE_DOWNWARD, FE_TONEAREST


def _init_msvcrt():
    """
    Load MS Visual Studio C Run-Time Library (float.h) rounding mode control functions.
    https://msdn.microsoft.com/library/e9b52ceh.aspx
    """
    global TO_ZERO, TOWARD_MINUS_INF, TOWARD_PLUS_INF, TO_NEAREST
    global set_rounding, get_rounding
    from ctypes import cdll
    msvcrt = cdll.msvcrt
    assert msvcrt._controlfp
    mask = 0x0300  # _MCW_RC
    set_rounding = lambda mode: True if msvcrt._controlfp(mode, mask) & mask == mode else False
    get_rounding = lambda: msvcrt._controlfp(0, 0) & mask
    TO_ZERO, TOWARD_PLUS_INF, TOWARD_MINUS_INF, TO_NEAREST = 0x0300, 0x0200, 0x0100, 0x000
    # _RC_CHOP,  _RC_UP, _RC_DOWN, _RC_NEAR


for _init_rounding in _init_libm, _init_msvcrt:
    try:
        _init_rounding()
        break
    except:
        pass
else:
    raise RuntimeError("Could not load rounding mode control functions.")

# Interval class.
# ---------------

class Interval:

    strict_operators = False
    certain_comparisons = True

    def __init__(self, value_1, value_2=None):
        # use Decimal as exact value holder (because of arbitrary precision)
        from decimal import Decimal
        # nextafter(x, y) returns next machine number after x in direction of y
        from numpy import nextafter

        # creating interval from middle value
        if not value_2:
            exact = Decimal(value_1)
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
        # creating interval from left and right edge
        else:
            exact_left = Decimal(value_1)
            exact_right = Decimal(value_2)
            if exact_left > exact_right:
                exact_left, exact_right = exact_right, exact_left
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

    def _process_other(self, other):
        """
        Helper method for overloaded operators.
        Will try to create Interval from other value if self.strict is false.
        :param other: numeric value or interval
        :return: other value as interval (if possible)
        """
        if isinstance(other, Interval):
            return other
        elif not self.strict_operators:
            try:
                return Interval(other)
            except:
                raise ValueError("Can't use other value from overloaded operator as numeric.")
        else:
            raise ValueError("Can't use overloaded operator with non-interval in strict mode.")

    # Operators' overloading.
    # Operations can be mixed with other numeric types
    #   interval is in non-strict mode.

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

    def __eq__(self, other):
        return Interval.iequal(self, self._process_other(other), certainly=self.certain_comparisons)

    def __ne__(self, other):
        return Interval.inotequal(self, self._process_other(other), certainly=self.certain_comparisons)

    # Arithmetic operations.
    # Proper arguments are Intervals.

    @staticmethod
    def iwidth(interval):
        set_rounding(TOWARD_PLUS_INF)
        ret = interval.rv - interval.lv
        set_rounding(TO_NEAREST)
        return ret

    @staticmethod
    def iadd(lint, rint):
        set_rounding(TOWARD_MINUS_INF)
        lv = lint.lv + rint.lv
        set_rounding(TOWARD_PLUS_INF)
        rv = lint.rv + rint.rv
        set_rounding(TO_NEAREST)
        return Interval(lv, rv)

    @staticmethod
    def isubtract(lint, rint):
        set_rounding(TOWARD_MINUS_INF)
        lv = lint.lv - rint.rv
        set_rounding(TOWARD_PLUS_INF)
        rv = lint.rv - rint.lv
        set_rounding(TO_NEAREST)
        return Interval(lv, rv)

    @staticmethod
    def imultiply(lint, rint):
        set_rounding(TOWARD_MINUS_INF)
        lv = min(lint.lv*rint.lv, lint.lv*rint.rv, lint.rv*rint.lv, lint.rv*rint.rv)
        set_rounding(TOWARD_PLUS_INF)
        rv = max(lint.lv*rint.lv, lint.lv*rint.rv, lint.rv*rint.lv, lint.rv*rint.rv)
        set_rounding(TO_NEAREST)
        return Interval(lv, rv)

    @staticmethod
    def idivide(lint, rint):
        if rint.lv <= 0.0 <= rint.rv:
            raise ZeroDivisionError("Division by an interval containing 0.")
        set_rounding(TOWARD_MINUS_INF)
        lv = min(lint.lv/rint.lv, lint.lv/rint.rv, lint.rv/rint.lv, lint.rv/rint.rv)
        set_rounding(TOWARD_PLUS_INF)
        rv = max(lint.lv/rint.lv, lint.lv/rint.rv, lint.rv/rint.lv, lint.rv/rint.rv)
        set_rounding(TO_NEAREST)
        return Interval(lv, rv)

    # todo: sin, cos, exp, tan...

    @staticmethod
    def iequal(lint, rint, certainly=True):
        if certainly:
            return lint.lv == lint.rv == rint.lv == rint.rv
        else:
            return lint.rv >= rint.lv and lint.lv <= rint.rv or rint.rv >= lint.lv and rint.lv <= lint.rv

    @staticmethod
    def inotequal(lint, rint, certainly=True):
        if certainly:
            return not Interval.iequal(lint, rint, certainly=False)
        else:
            return not Interval.iequal(lint, rint, certainly=True)

    # Some constants.

    @staticmethod
    def ipi():
        return Interval('3.1415926535897932384626433832795028841972')

    @staticmethod
    def ie():
        return Interval('2.7182818284590452353602874713526624977572')

    @staticmethod
    def izero():
        return Interval('0')

    @staticmethod
    def ione():
        return Interval('1')

    # Interval representation as float and string.

    def __str__(self):
        return "<{0:0.20f}; {1:0.20f}>".format(self.lv, self.rv)

    def __repr__(self):
        return "Interval({0:0.20f}, {1:0.20f})".format(self.lv, self.rv)

    def __float__(self):
        return self.lv + Interval.iwidth(self) / 2
