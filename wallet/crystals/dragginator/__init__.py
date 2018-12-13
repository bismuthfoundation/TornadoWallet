from modules.basehandlers import CrystalHandler


DEFAULT_THEME_PATH = 'crystals/dragginator/themes/default'


class DragginatorHandler(CrystalHandler):

    async def credits(self, params=None):
        self.render("about_credits.html", bismuth=self.bismuth_vars)

    async def network(self, params=None):
        self.render("about_network.html", bismuth=self.bismuth_vars)

    async def get(self, command=''):
        command, *params = command.split('/')
        if not command:
            command = 'credits'
        await getattr(self, command)(params)
