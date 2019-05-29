#
# Copyright (c) 2014-2015 Sylvain Peyrefitte
#
# This file is part of rdpy.
#
# rdpy is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

"""
GDI order structure
"""

from rdpy.core import log
from rdpy.core.error import InvalidExpectedDataException
from rdpy.core.type import CompositeType, UInt8, String, FactoryType, SInt8, SInt16Le, UInt16Le, sizeof, ArrayType
import data

class ControlFlag(object):
    """
    @summary: Class order of drawing order
    @see: http://msdn.microsoft.com/en-us/library/cc241586.aspx
    """
    TS_STANDARD = 0x01
    TS_SECONDARY = 0x02
    TS_BOUNDS = 0x04
    TS_TYPE_CHANGE = 0x08
    TS_DELTA_COORDINATES = 0x10
    TS_ZERO_BOUNDS_DELTAS = 0x20
    TS_ZERO_FIELD_BYTE_BIT0 = 0x40
    TS_ZERO_FIELD_BYTE_BIT1 = 0x80
    
class OrderType(object):
    """
    @summary: Primary order type
    @see: http://msdn.microsoft.com/en-us/library/cc241586.aspx
    """
    TS_ENC_DSTBLT_ORDER = 0x00
    TS_ENC_PATBLT_ORDER = 0x01
    TS_ENC_SCRBLT_ORDER = 0x02
    TS_ENC_DRAWNINEGRID_ORDER = 0x07
    TS_ENC_MULTI_DRAWNINEGRID_ORDER = 0x08
    TS_ENC_LINETO_ORDER = 0x09
    TS_ENC_OPAQUERECT_ORDER = 0x0A
    TS_ENC_SAVEBITMAP_ORDER = 0x0B
    TS_ENC_MEMBLT_ORDER = 0x0D
    TS_ENC_MEM3BLT_ORDER = 0x0E
    TS_ENC_MULTIDSTBLT_ORDER = 0x0F
    TS_ENC_MULTIPATBLT_ORDER = 0x10
    TS_ENC_MULTISCRBLT_ORDER = 0x11
    TS_ENC_MULTIOPAQUERECT_ORDER = 0x12
    TS_ENC_FAST_INDEX_ORDER = 0x13
    TS_ENC_POLYGON_SC_ORDER = 0x14
    TS_ENC_POLYGON_CB_ORDER = 0x15
    TS_ENC_POLYLINE_ORDER = 0x16
    TS_ENC_FAST_GLYPH_ORDER = 0x18
    TS_ENC_ELLIPSE_SC_ORDER = 0x19
    TS_ENC_ELLIPSE_CB_ORDER = 0x1A
    TS_ENC_INDEX_ORDER = 0x1B

class SecOrderType(object):
    TS_CACHE_BITMAP_UNCOMPRESSED = 0x00
    TS_CACHE_COLOR_TABLE = 0x01
    TS_CACHE_BITMAP_COMPRESSED = 0x02
    TS_CACHE_GLYPH = 0x03
    TS_CACHE_BITMAP_UNCOMPRESSED_REV2 = 0x04
    TS_CACHE_BITMAP_COMPRESSED_REV2 = 0x05
    TS_CACHE_BRUSH = 0x07
    TS_CACHE_BITMAP_COMPRESSED_REV3 = 0x08

    
class CoordField(CompositeType):
    """
    @summary: used to describe a value in the range -32768 to 32767
    @see: http://msdn.microsoft.com/en-us/library/cc241577.aspx
    """
    def __init__(self, isDelta, conditional = lambda:True):
        """
        @param isDelta: callable object to know if coord field is in delta mode
        @param conditional: conditional read or write type
        """
        CompositeType.__init__(self, conditional = conditional)
        self.delta = SInt8(conditional = isDelta)
        self.coordinate = SInt16Le(conditional = isDelta)
    
class PrimaryDrawingOrder(CompositeType):
    """
    @summary: GDI Primary drawing order
    @see: http://msdn.microsoft.com/en-us/library/cc241586.aspx
    """
    def __init__(self, order = None):
        CompositeType.__init__(self)
        self.controlFlags = UInt8()
        self.orderType = UInt8()
        
        def OrderFactory():
            """
            Closure for capability factory
            """
            for c in [DstBltOrder, MemBltOrder]:
                if self.orderType.value == c._ORDER_TYPE_:
                    return c(self.controlFlags)
            log.debug("unknown Order type : %s"%hex(self.orderType.value))
            #read entire packet
            return String()
        
        if order is None:
            order = FactoryType(OrderFactory)
        elif not "_ORDER_TYPE_" in order.__class__.__dict__:
            log.debug(order.__class__.__dict__)
            raise InvalidExpectedDataException("Try to send an invalid order block")
        else:
            self.controlFlags = UInt8(ControlFlag.TS_STANDARD | ControlFlag.TS_TYPE_CHANGE | order._ZERO_FIELD_BYTE_BIT0_ | order._ZERO_FIELD_BYTE_BIT1_ )
            self.orderType = UInt8(order._ORDER_TYPE_)
            self.order = order

class SecondaryDrawingOrder(CompositeType):
    """
    @summary: GDI Secondary drawing order
    @see: http://msdn.microsoft.com/en-us/library/cc241586.aspx
    """
    def __init__(self, order = None):
        CompositeType.__init__(self)
        self.controlFlags = UInt8()
        self.orderLength = SInt16Le(lambda:sizeof(self.order) + 6 - 13) # Length of order + header bytes - 13
        self.extraFlags = UInt16Le()
        self.orderType = UInt8()
        
        def OrderFactory():
            """
            Closure for capability factory
            """
            for c in [CacheBitmapOrder]:
                if self.orderType.value == c._ORDER_TYPE_:
                    return c(self.controlFlags)
            log.debug("unknown Order type : %s"%hex(self.orderType.value))
            #read entire packet
            return String()
        
        if order is None:
            order = FactoryType(OrderFactory)
        elif not "_ORDER_TYPE_" in order.__class__.__dict__:
            log.debug(order.__class__.__dict__)
            raise InvalidExpectedDataException("Try to send an invalid order block")
        else:
            self.controlFlags = UInt8(ControlFlag.TS_STANDARD | ControlFlag.TS_SECONDARY | ControlFlag.TS_TYPE_CHANGE )
            self.extraFlags = UInt16Le(order._EXTRA_FLAGS_)
            self.orderType = UInt8(order._ORDER_TYPE_)
            self.order = order


class DstBltOrder(CompositeType):
    """
    @summary: The DstBlt Primary Drawing Order is used to paint 
                a rectangle by using a destination-only raster operation.
    @see: http://msdn.microsoft.com/en-us/library/cc241587.aspx
    """
    # Zero Field Bytes for the Control Flags
    _ZERO_FIELD_BYTE_BIT0_ = 0x0
    _ZERO_FIELD_BYTE_BIT1_ = 0x0
    # Order type
    _ORDER_TYPE_ = OrderType.TS_ENC_DSTBLT_ORDER
    #negotiation index
    _NEGOTIATE_ = 0x00
    
    def __init__(self, controlFlag):
        CompositeType.__init__(self)
        #only one field
        self.fieldFlag = UInt8(conditional = lambda:(controlFlag.value & ControlFlag.TS_ZERO_FIELD_BYTE_BIT0 == 0 and controlFlag.value & ControlFlag.TS_ZERO_FIELD_BYTE_BIT1 == 0))
        self.nLeftRect = CoordField(lambda:not controlFlag.value & ControlFlag.TS_DELTA_COORDINATES == 0)
        self.nTopRect = CoordField(lambda:not controlFlag.value & ControlFlag.TS_DELTA_COORDINATES == 0)
        self.nWidth = CoordField(lambda:not controlFlag.value & ControlFlag.TS_DELTA_COORDINATES == 0)
        self.nHeight = CoordField(lambda:not controlFlag.value & ControlFlag.TS_DELTA_COORDINATES == 0)
        self.bRop = CoordField(lambda:not controlFlag.value & ControlFlag.TS_DELTA_COORDINATES == 0)

class MemBltOrder(CompositeType):
    """
    @summary: The MemBlt Primary Drawing Order is used to render a 
                bitmap stored in the bitmap cache or offscreen bitmap cache to the screen.
    @see: https://docs.microsoft.com/en-us/openspecs/windows_protocols/ms-rdpegdi/84c2ec2f-f776-405b-9b48-6894a28b1b14
    """
    # Zero Field Bytes for the Control Flags
    _ZERO_FIELD_BYTE_BIT0_ = 0x40 # Normally 0x40

    # MemBltOrder is a 2 Byte field Flag, this should always be 0
    _ZERO_FIELD_BYTE_BIT1_ = 0x00 # Normally 0x80

    # order type
    _ORDER_TYPE_ = OrderType.TS_ENC_MEMBLT_ORDER

    # negotiation index
    _NEGOTIATE_ = 0x00
    
    def __init__(self, controlFlag):
        CompositeType.__init__(self)
        #only one field
        self.fieldFlag = UInt8(0x0)
        self.cacheId = UInt16Le()
        self.nLeftRect = CoordField(lambda:not controlFlag.value & ControlFlag.TS_DELTA_COORDINATES == 0)
        self.nTopRect = CoordField(lambda:not controlFlag.value & ControlFlag.TS_DELTA_COORDINATES == 0)
        self.nWidth = CoordField(lambda:not controlFlag.value & ControlFlag.TS_DELTA_COORDINATES == 0)
        self.nHeight = CoordField(lambda:not controlFlag.value & ControlFlag.TS_DELTA_COORDINATES == 0)
        self.bRop = CoordField(lambda:not controlFlag.value & ControlFlag.TS_DELTA_COORDINATES == 0)
        self.nXSrc = CoordField(lambda:not controlFlag.value & ControlFlag.TS_DELTA_COORDINATES == 0)
        self.nYSrc = CoordField(lambda:not controlFlag.value & ControlFlag.TS_DELTA_COORDINATES == 0)
        self.cacheIndex = UInt16Le()

class CacheBitmapOrder(CompositeType):
    """
    @ summary: The Cache Bitmap secondary order Revision 1
    @ see: https://docs.microsoft.com/en-us/openspecs/windows_protocols/ms-rdpegdi/c9365b32-0be5-47c9-af1a-feba2ea1ee9f
    """
    # Extra Flags
    _EXTRA_FLAGS_ = 0x00

    # Order Type
    _ORDER_TYPE_ = SecOrderType.TS_CACHE_BITMAP_UNCOMPRESSED

    def __init__(self, cacheId = 0, bitmapWidth = 32, bitmapHeight = 32, bitmapBitsPerPel = 24, cacheIndex = 0, bitmapDataStream = "", compressed = False, bitmapComprHdr = ""):
        CompositeType.__init__(self)
        if not compressed:
            self._ORDER_TYPE_ = SecOrderType.TS_CACHE_BITMAP_UNCOMPRESSED
            self._EXTRA_FLAGS_ = 0x0400  # If We are uncompressed we can skip the bitmapComprHdr field
        else:
            self._ORDER_TYPE_ = SecOrderType.TS_CACHE_BITMAP_COMPRESSED
            if sizeof(bitmapComprHdr) == 0:
                self._EXTRA_FLAGS_ = 0x0400 # If we don't have a ComprHdr, we can skip the bitmapComprHdr

        self.cacheId = UInt8(cacheId)
        self.pad1Octet = UInt8()
        self.bitmapWidth = UInt8(bitmapWidth)
        self.bitmapHeight = UInt8(bitmapHeight)
        self.bitmapBitsPerPel = UInt8(bitmapBitsPerPel)
        self.bitmapLength = UInt16Le(lambda:sizeof(self.bitmapComprHdr) + sizeof(self.bitmapDataStream))
        self.bitmapLength = UInt16Le(0x00)
        self.cacheIndex = UInt16Le(cacheIndex)
        if self._EXTRA_FLAGS_ == 0x00:
            self.bitmapComprHdr = String(bitmapComprHdr)
        self.bitmapDataStream = String(bitmapDataStream)

class CacheBitmap2Order(CompositeType):
    """
    @ summary: The Cache Bitmap secondary order Revision 1
    @ see: https://docs.microsoft.com/en-us/openspecs/windows_protocols/ms-rdpegdi/c9365b32-0be5-47c9-af1a-feba2ea1ee9f
    """
    # Extra Flags
    _EXTRA_FLAGS_ = 0x00

    # Order Type
    _ORDER_TYPE_ = SecOrderType.TS_CACHE_BITMAP_UNCOMPRESSED_REV2

    def __init__(self, cacheId = 0, bitmapWidth = 32, bitmapHeight = 32, bitmapBitsPerPel = 24, cacheIndex = 0, bitmapDataStream = "", compressed = False, bitmapComprHdr = ""):
        CompositeType.__init__(self)
        if not compressed:
            self._ORDER_TYPE_ = SecOrderType.TS_CACHE_BITMAP_UNCOMPRESSED_REV2
            self._EXTRA_FLAGS_ = 0x08  # If We are uncompressed we can skip the bitmapComprHdr field
        else:
            self._ORDER_TYPE_ = SecOrderType.TS_CACHE_BITMAP_COMPRESSED_REV2
            if sizeof(bitmapComprHdr) == 0:
                self._EXTRA_FLAGS_ = 0x08 # If we don't have a ComprHdr, we can skip the bitmapComprHdr

        self.bitmapWidth = UInt16Le()
        self.bitmapHeight = UInt16Le()
        
        if self._EXTRA_FLAGS_ & 0x08 == 0:
            self.bitmapComprHdr = String(bitmapComprHdr)
        self.bitmapDataStream = String(bitmapDataStream)

class CacheColorTableOrder(CompositeType):
    # Extra Flags
    _EXTRA_FLAGS_ = 0x00
    
    # Order Type
    _ORDER_TYPE_ = SecOrderType.TS_CACHE_COLOR_TABLE

    def __init__(self, colors = [], cacheId = 0):
        CompositeType.__init__(self)
        self.cacheId = UInt8(cacheId)
        self.numberColors = UInt16Le(lambda:len(self.colorTable._array))
        self.colorTable = ArrayType(data.ColorQuad, init = colors, readLen = self.numberColors)
