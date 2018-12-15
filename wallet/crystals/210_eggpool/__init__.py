"""
Dragginator Crystal for Tornado wallet
"""
from os import path

from modules.basehandlers import CrystalHandler
from modules.helpers import base_path, get_api_10

DEFAULT_THEME_PATH = path.join(base_path(), 'crystals/210_eggpool/themes/default')


class EggpoolHandler(CrystalHandler):

    async def about(self, params=None):
        url = 'https://eggpool.net/index.php?action=api&miner={}&type=v2'.format(self.bismuth_vars['address'])
        api = get_api_10(url, is_json=True)  # gets as dict, and cache for 10 min
        print(api)
        """
        # detail
        {'last_event': 1544822567, 
        'BIS': {'min_payout': 0, 'total_paid': 3248.8013716867, 'immature': 0.34210355367913, 'balance': 5.8549067988689}, 
        'round': {'shares': 4, 'hr': 7791, 'mhr': 7790},
        'lastround': {'mhr': 7775, 'hr': 7755, 'shares': 16}, 
        'workers': {'count': 2, 
            'detail': {
                'Hive-devrig': [3969.5, 1544822567, [3967, 3968, 3966, 3966, 3968, 3971, 3972, 3978, 3975, 3973, 3976, 3975, 3970], [6, 5, 10, 5, 13, 3, 7, 1, 8, 5, 10, 9, 2]], 
                'Egg Dev Red': [3820.5, 1544822501, [3805, 3831, 3806, 3819, 3807, 3828, 3805, 3859, 3818, 3840, 3823, 3800, 3821], [5, 4, 8, 6, 5, 6, 3, 4, 12, 5, 8, 7, 2]]}, 
                'missing_count': 0}, 
                'payouts': [['2018-12-14 08:17:14', 12.157054977414, ' '], ['2018-12-13 08:17:07', 11.277245257875, ' '], ['2018-12-12 08:17:18', 15.654745857231, ' '], ['2018-12-10 20:17:36', 11.841785656065, ' '], ['2018-12-09 20:17:18', 14.459878509432, ' '], ['2018-12-08 08:17:42', 15.839356315061, ' '], ['2018-12-06 20:17:11', 11.431415310436, ' '], ['2018-12-05 20:17:29', 16.995411304982, ' '], ['2018-12-04 08:17:35', 10.582438046254, ' '], ['2018-12-03 08:17:44', 10.179619238548, ' ']]
                }
        # v2
        {'last_event': 1544822867, 
        'BIS': {'min_payout': 0, 'total_paid': 3248.8013716867, 'immature': 0.34210355367913, 'balance': 5.8549067988689}, 
        'round': {'shares': 4, 'hr': 7791, 'mhr': 7790}, 
        'lastround': {'mhr': 7775, 'hr': 7755, 'shares': 16}, 
        'workers': {'count': 2, 
            'detail': {
                'Hive-devrig': [3969.5, 1544822867], 
                'Egg Dev Red': [3820.5, 1544822801]}, 
                'missing_count': 0}
            }

        """
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
