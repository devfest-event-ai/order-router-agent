# src/router/geo_routing.py

from typing import Dict, Optional, Tuple
from src.schemas.order_schema import UnifiedOrder

class WarehouseLocation:
    """Representasi warehouse dengan lokasi dan kapasitas."""
    def __init__(self, warehouse_id: str, city: str, province: str, is_active: bool = True):
        self.warehouse_id = warehouse_id
        self.city = city.upper()
        self.province = province.upper()
        self.is_active = is_active

class GeoRouter:
    """
    Routing logic berdasarkan lokasi geografis.
    Memilih warehouse terdekat yang serviceable untuk kota tujuan.
    """
    
    # Database warehouse
    def __init__(self):
        self.warehouses: Dict[str, WarehouseLocation] = {
            "WH_JKT": WarehouseLocation("WH_JKT", "JAKARTA", "DKI JAKARTA"),
            "WH_TNG": WarehouseLocation("WH_TNG", "TANGERANG", "BANTEN"),
            "WH_BDG": WarehouseLocation("WH_BDG", "BANDUNG", "JAWA BARAT"),
            "WH_SBY": WarehouseLocation("WH_SBY", "SURABAYA", "JAWA TIMUR"),
            "WH_MDN": WarehouseLocation("WH_MDN", "MEDAN", "SUMATERA UTARA"),
        }
        
        # Mapping kota ke warehouse terdekat (bisa expanded)
        self.city_to_warehouse: Dict[str, str] = {
            "JAKARTA": "WH_JKT",
            "JAKARTA PUSAT": "WH_JKT",
            "JAKARTA SELATAN": "WH_JKT",
            "JAKARTA UTARA": "WH_JKT",
            "JAKARTA BARAT": "WH_JKT",
            "JAKARTA TIMUR": "WH_JKT",
            "TANGERANG": "WH_TNG",
            "KAB. TANGERANG": "WH_TNG",
            "BANDUNG": "WH_BDG",
            "KAB. BANDUNG": "WH_BDG",
            "SURABAYA": "WH_SBY",
            "SIDOARJO": "WH_SBY",
            "GRISIK": "WH_SBY",
            "MEDAN": "WH_MDN",
            "DELI SERDANG": "WH_MDN",
        }
        
        # Serviceable areas untuk COD (beberapa area mungkin tidak support COD)
        self.cod_unserviceable_cities = {
            "KAB. TANGERANG",  # Contoh: area terpencil tidak support COD
        }

    def select_warehouse(self, order: UnifiedOrder) -> Dict:
        """
        Pilih warehouse berdasarkan kota tujuan.
        Return: warehouse_id, estimated_delivery_days, is_cod_available
        """
        target_city = order.shipping_address.city.upper()
        target_province = order.shipping_address.province.upper()
        
        # 1. Cari warehouse mapping
        warehouse_id = self.city_to_warehouse.get(target_city)
        
        # 2. Fallback: cari berdasarkan province
        if not warehouse_id:
            warehouse_id = self._find_warehouse_by_province(target_province)
        
        # 3. Jika tidak ketemu, pakai default (Jakarta)
        if not warehouse_id:
            warehouse_id = "WH_JKT"
        
        # 4. Cek COD availability
        is_cod_available = target_city not in self.cod_unserviceable_cities
        
        # 5. Estimasi delivery days (logika sederhana)
        est_days = self._calculate_delivery_days(target_city, target_province)
        
        return {
            "warehouse_id": warehouse_id,
            "warehouse_city": self.warehouses[warehouse_id].city,
            "estimated_delivery_days": est_days,
            "is_cod_available": is_cod_available,
            "routing_note": "Routed to nearest warehouse"
        }

    def _find_warehouse_by_province(self, province: str) -> Optional[str]:
        """Fallback: cari warehouse di provinsi yang sama."""
        for wh_id, wh in self.warehouses.items():
            if wh.province == province:
                return wh_id
        return None

    def _calculate_delivery_days(self, city: str, province: str) -> int:
        """Estimasi hari pengiriman berdasarkan lokasi."""
        # Java: 1-2 hari
        if "JAWA" in province or "DKI" in province or "BANTEN" in province or "DI YOGYAKARTA" in province:
            return 2
        
        # Sumatera, Bali, NTB, NTT: 3-4 hari
        if "SUMATERA" in province or "BALI" in province or "NUSA" in province:
            return 4
        
        # Kalimantan, Sulawesi: 5-6 hari
        if "KALIMANTAN" in province or "SULAWESI" in province:
            return 5
        
        # Papua, Maluku: 7+ hari
        if "PAPUA" in province or "MALUKU" in province:
            return 7
        
        # Default
        return 3

    def validate_routing(self, order: UnifiedOrder) -> Dict:
        """
        Validasi apakah order bisa dirutekan ke warehouse.
        """
        routing = self.select_warehouse(order)
        errors = []
        warnings = []
        
        # Cek COD availability
        if order.payment.method == "COD (Bayar di Tempat)" and not routing["is_cod_available"]:
            errors.append(
                f"COD_UNAVAILABLE: COD tidak tersedia untuk {order.shipping_address.city}. "
                f"Silakan pilih metode pembayaran lain."
            )
        
        # Warning untuk remote area
        if routing["estimated_delivery_days"] > 5:
            warnings.append(
                f"REMOTE_AREA: Estimasi pengiriman {routing['estimated_delivery_days']} hari. "
                f"Customer should be informed."
            )
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "routing_info": routing
        }