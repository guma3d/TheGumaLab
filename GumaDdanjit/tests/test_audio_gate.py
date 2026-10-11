from unittest.mock import patch
import pytest
from app.core import shopping


def test_one_quiet_cut_blocks_join_even_with_normal_neighbors(tmp_path):
    levels = [{'integrated_lufs': -16, 'true_peak_dbfs': -3},
              {'integrated_lufs': -39, 'true_peak_dbfs': -22}]
    with patch.object(shopping.media, 'duration', return_value=4), \
         patch.object(shopping.bgm, 'measure_audio', side_effect=levels), \
         patch.object(shopping.media, 'run') as render:
        with pytest.raises(ValueError, match='CUT 2'):
            shopping.join_smooth(['one.mp4', 'two.mp4'], tmp_path/'out.mp4')
        render.assert_not_called()


def test_audible_cuts_can_join(tmp_path):
    with patch.object(shopping.media, 'duration', return_value=4), \
         patch.object(shopping.bgm, 'measure_audio', return_value={
             'integrated_lufs': -18, 'true_peak_dbfs': -4}), \
         patch.object(shopping.media, 'run') as render:
        shopping.join_smooth(['one.mp4', 'two.mp4'], tmp_path/'out.mp4')
        render.assert_called_once()
