from models.example import Item

# Servicio para manejar la lógica de negocio relacionada con "Item"
class ItemService:
    @staticmethod
    def calculate_discounted_price(item: Item, discount: float) -> float:
        """
        Calcula el precio con descuento para un item.
        
        :param item: El objeto Item que contiene el precio base.
        :param discount: El porcentaje de descuento (por ejemplo, 0.1 para 10%).
        :return: El precio después de aplicar el descuento.
        """
        if not (0 <= discount <= 1):
            raise ValueError("El descuento debe estar entre 0 y 1.")
        return item.price * (1 - discount)

    @staticmethod
    def format_item_data(item: Item) -> dict:
        """
        Devuelve una representación formateada de un item.
        
        :param item: El objeto Item.
        :return: Un diccionario con los datos del item formateados.
        """
        return {
            "nombre": item.name.upper(),
            "descripcion": item.description or "Sin descripción",
            "precio_original": item.price,
        }
