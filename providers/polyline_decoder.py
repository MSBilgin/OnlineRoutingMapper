from typing import List, Tuple

class PolylineDecoder:
    
    @staticmethod
    def decode(encoded: str, precision: int = 5) -> List[Tuple[float, float]]:
        """
        :param encoded: Encoded polyline dizgesi
        :param precision: Enlem/ boylam için ondalık hassasiyeti (genellikle 5 veya 6)
        :return: [(lat, lon), ...] listesi
        :raises ValueError: Biçim bozuksa
        """
        if not isinstance(encoded, str):
            raise TypeError("encoded must be a string")
        if precision < 0:
            raise ValueError("precision must be non-negative")

        coords: List[Tuple[float, float]] = []
        index = 0
        lat = 0
        lon = 0
        factor = 10 ** precision

        length = len(encoded)

        def _next_value() -> int:
            nonlocal index
            result = 0
            shift = 0
            # Her değer 5-bit parçalara bölünmüş; 0x20 (32) devam biti
            while True:
                if index >= length:
                    # string erken bittiyse biçim hatası
                    raise ValueError("Malformed polyline: premature ending")
                b = ord(encoded[index]) - 63
                index += 1
                if b < 0 or b > 95:
                    # Geçersiz karakter (normalde 63..95 arası olmalı)
                    raise ValueError("Malformed polyline: invalid character")
                result |= (b & 0x1F) << shift
                shift += 5
                if (b & 0x20) == 0:
                    break
            # İmzalı tamsayıya dönüştür
            return ~(result >> 1) if (result & 1) else (result >> 1)

        while index < length:
            dlat = _next_value()
            dlon = _next_value()
            lat += dlat
            lon += dlon
            coords.append((lat / factor, lon / factor))

        return coords
