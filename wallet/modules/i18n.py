"""
i18n / l18n helpers
"""


def get_spend_type(_, spend:str) -> str:
    if spend is None:
        return _("No protection")
    if spend == 'PIN':
        return _("PIN Code")
    if spend == 'YUBICO':
        return _("YUBICO")
    if spend == 'U2F':
        return _("U2F Token")


def get_dt_language(_):
    """Gives the translations for the datatables jquery plugin."""
    # TODO: handle better than that
    # https://datatables.net/plug-ins/i18n
    DT_LANGUAGE = '   language: {\n'
    DT_LANGUAGE += 'processing: "{}",\n'.format(_('DT:Processing...'))
    DT_LANGUAGE += 'search: "{}",\n'.format(_('DT:Search&nbsp;...'))
    DT_LANGUAGE += 'lengthMenu: "{}",\n'.format(_('DT:Display _MENU_ elements'))
    DT_LANGUAGE += 'info: "{}",\n'.format(_('DT:Display element _START_ to _END_ from _TOTAL_ elements'))
    DT_LANGUAGE += 'infoEmpty: "{}",\n'.format(_('DT:Nothing to display'))
    DT_LANGUAGE += 'infoFiltered: "{}",\n'.format(_('DT:filtered from _MAX_ total elements'))
    DT_LANGUAGE += 'infoPostFix: "{}",\n'.format('')
    DT_LANGUAGE += 'loadingRecords: "{}",\n'.format(_('DT:Loading...'))
    DT_LANGUAGE += 'zeroRecords: "{}",\n'.format(_('DT:Nothing to display'))
    DT_LANGUAGE += 'emptyTable: "{}",\n'.format(_('DT:No data in the table'))
    DT_LANGUAGE += 'paginate: {\n'
    DT_LANGUAGE += 'first: "{}",\n'.format(_('DT:First'))
    DT_LANGUAGE += 'previous: "{}",\n'.format(_('DT:Previous'))
    DT_LANGUAGE += 'next: "{}",\n'.format(_('DT:Next'))
    DT_LANGUAGE += 'last: "{}"\n'.format(_('DT:Last'))
    DT_LANGUAGE += '},\n'
    DT_LANGUAGE += 'aria: {\n'
    DT_LANGUAGE += 'sortAscending: "{}",\n'.format(_('DT:Sort by ascending order'))
    DT_LANGUAGE += 'sortDescending: "{}"\n'.format(_('DT:Sort by descending order'))
    DT_LANGUAGE += '}\n}'
    return DT_LANGUAGE

