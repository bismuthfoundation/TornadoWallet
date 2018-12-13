"""
Dragginator Crystal for Tornado wallet
"""

from modules.basehandlers import CrystalHandler


DEFAULT_THEME_PATH = 'crystals/dragginator/themes/default'


class DragginatorHandler(CrystalHandler):

    async def about(self, params=None):
        self.render("about.html", bismuth=self.bismuth_vars)

    async def get(self, command=''):
        command, *params = command.split('/')
        if not command:
            command = 'about'
        await getattr(self, command)(params)

    def get_template_path(self):
        """Override to customize template path for each handler.

        By default, we use the ``template_path`` application setting.
        Return None to load templates relative to the calling file.
        """
        return DEFAULT_THEME_PATH
