"""加载本项目里复制过来的排盘函数。"""


def load_bazi():
    """
    :return: (compute_paipan_detail, compute_current_dayun)
    """
    from .rules.bazi.paipan_xiyongshen import compute_current_dayun, compute_paipan_detail

    return compute_paipan_detail, compute_current_dayun


def load_ziwei():
    """
    :return: (parse_ziwei_request, calculate_ziwei, ZiweiInputError, ZiweiEngineError)
    """
    from .rules.ziwei.ziwei_engine import (
        ZiweiEngineError,
        ZiweiInputError,
        calculate_ziwei,
        parse_ziwei_request,
    )

    return parse_ziwei_request, calculate_ziwei, ZiweiInputError, ZiweiEngineError
