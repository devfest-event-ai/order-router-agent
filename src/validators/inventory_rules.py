# src/validators/inventory_rules.py

from typing import List, Dict, Any, Tuple
from src.schemas.order_schema import UnifiedOrder

class MockInventory:
    """
    Simulasi database stok barang.
    Di production, ini akan digantikan oleh API (seperti TradeGecko atau database SQL).
    """
    
    # Data awal (Seed Data) - Bisa ditambah sesuai kebutuhan test
    def __init__(self):
        self.stock: Dict[str, int] = {
            "Celengan": 150,
            "Laptop Gaming": 5,
            "Mouse Wireless": 200,
            "Keyboard Mechanical": 0,  # Stok Habis
            "Kaos Polos": 1000
        }

    def get_stock(self, product_name: str) -> int:
        """Mengecek jumlah stok untuk produk tertentu."""
        # Return 0 jika produk tidak dikenali (safety check)
        return self.stock.get(product_name, 0)

    def deduct_stock(self, product_name: str, quantity: int):
        """Mengurangi stok (Simulasi pengurangan stok saat order valid)."""
        if product_name in self.stock:
            self.stock[product_name] -= quantity

class InventoryValidator:
    """
    Memvalidasi ketersediaan stok dalam sebuah order.
    """
    
    def __init__(self, inventory: MockInventory):
        self.inventory = inventory

    def validate(self, order: UnifiedOrder) -> Dict[str, Any]:
        """
        Mengecek setiap item di order terhadap stok tersedia.
        """
        errors: List[str] = []
        warnings: List[str] = []
        items_to_deduct: List[Tuple[str, int]] = []

        for item in order.items:
            available_stock = self.inventory.get_stock(item.product_name)
            
            # 1. Cek apakah produk dikenali
            if available_stock == 0 and item.product_name not in self.inventory.stock:
                errors.append(f"UNKNOWN_PRODUCT: '{item.product_name}' tidak ditemukan dalam database.")
                continue

            # 2. Cek kecukupan stok
            if item.quantity > available_stock:
                errors.append(
                    f"INSUFFICIENT_STOCK: '{item.product_name}' hanya tersisa {available_stock} unit, "
                    f"sedangkan dipesan {item.quantity} unit."
                )
            else:
                # Jika stok cukup, masukkan ke daftar untuk dikurangi nanti
                items_to_deduct.append((item.product_name, item.quantity))

        # 3. Jika valid, kurangi stok (Simulasi commit transaction)
        if not errors:
            for prod_name, qty in items_to_deduct:
                self.inventory.deduct_stock(prod_name, qty)
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "updated_stock": True if not errors else False
        }