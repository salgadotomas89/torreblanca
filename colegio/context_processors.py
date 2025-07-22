from .models import Menu, MenuItem, AppearanceSettings

def menu_items_processor(request):
    """
    Context processor que proporciona los items del menú ordenados y organizados
    """
    try:
        menu_principal = Menu.objects.get(nombre='Menu Principal')
        menu_items = MenuItem.objects.filter(menu=menu_principal).order_by('orden')
        
        # Filtrar según si el usuario está autenticado
        if request.user.is_authenticated:
            # Usuario logueado ve todos los items
            items_filtrados = menu_items
        else:
            # Usuario no logueado solo ve items públicos
            items_filtrados = menu_items.filter(solo_usuarios_logueados=False)
        
        # Separar items normales y mega menús
        items_normales = items_filtrados.filter(es_mega_menu=False)
        mega_menus = items_filtrados.filter(es_mega_menu=True)
        
        return {
            'menu_items': items_normales,
            'mega_menus': mega_menus
        }
    except Menu.DoesNotExist:
        return {
            'menu_items': [],
            'mega_menus': []
        }

def redes_sociales_processor(request):
    """
    Context processor que proporciona las URLs de redes sociales
    """
    try:
        apariencia = AppearanceSettings.objects.first()
        if apariencia:
            return {
                'redes_sociales': {
                    'facebook': apariencia.facebook_url,
                    'twitter': apariencia.twitter_url,
                    'instagram': apariencia.instagram_url,
                    'youtube': apariencia.youtube_url,
                }
            }
    except AppearanceSettings.DoesNotExist:
        pass
    
    return {
        'redes_sociales': {
            'facebook': None,
            'twitter': None,
            'instagram': None,
            'youtube': None,
        }
    }