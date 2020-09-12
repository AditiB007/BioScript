import pytest

from shared.bs_exceptions import InvalidOperation
from tests.frontend.front_end_base import FrontEndBase


@pytest.mark.frontend
@pytest.mark.target
@pytest.mark.instructions
@pytest.mark.MFSim
class TestMFSim(FrontEndBase):
    """
        These tests are very rudimentary, as they simply count the number
        of various elements of an MFSim CFG/DAGs:
        expected for each will be a list of the elements:
        [num_cgs, num_transfers, num_dags, num_detects,
                num_dispense, num_dispose, num_edges, num_heats,
                num_mixes, num_splits, num_exps]
        Added num_exps to better tell if the cfg file remains the same after changes
    """
     #begin simple unit tests
    def test_mix(self, get_visitor):
        file = "test_cases/mix/ir_sisd.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([0, 0, 1, 0, 2, 0, 2, 0, 1, 0, 0])
        assert expected == counts


    def test_heat(self, get_visitor):
        file = "test_cases/heat/ir_sisd.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([0, 0, 1, 0, 1, 0, 1, 1, 0, 0, 0])
        assert expected == counts

    def test_dispose(self, get_visitor):
        file = "test_cases/dispose/ir_sisd.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([0, 0, 1, 0, 1, 1, 1, 0, 0, 0, 0])
        assert expected == counts

    def test_dispense(self, get_visitor):
        file = "test_cases/dispense/ir_sisd.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0])
        assert expected == counts

    def test_detect(self, get_visitor):
        file = "test_cases/detect/ir_sisd_no_index.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([0, 0, 1, 1, 1, 0, 1, 0, 0, 0, 0])
        assert expected == counts

    def test_split(self, get_visitor):
        file = "test_cases/split/ir_sisd.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([0, 0, 1, 0, 1, 0, 3, 0, 0, 3, 0])
        assert expected == counts

    # begin new split size and combination testing
    def test_split_simple_size2(self, get_visitor):
        file = "test_cases/split/simple_size2.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([0, 0, 1, 0, 2, 2, 5, 0, 1, 1, 0])
        assert expected == counts

    def test_split_simple_size4(self, get_visitor):
        file = "test_cases/split/simple_size4.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([0, 0, 1, 0, 2, 4, 9, 0, 1, 3, 0])
        assert expected == counts

    def test_split_simple_size8(self, get_visitor):
        file = "test_cases/split/simple_size8.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([0, 0, 1, 0, 2, 8, 17, 0, 1, 7, 0])
        assert expected == counts

    def test_split_size4_detect(self, get_visitor):
        file = "test_cases/split/size4_detect.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([0, 0, 1, 1, 2, 4, 10, 0, 1, 3, 0])
        assert expected == counts

    def test_split_size4_detect_mix(self, get_visitor):
        file = "test_cases/split/size4_detect_mix.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([0, 0, 1, 1, 3, 4, 12, 0, 2, 3, 0])
        assert expected == counts

    def test_split_size4_heat(self, get_visitor):
        file = "test_cases/split/size4_heat.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([0, 0, 1, 0, 2, 4, 10, 1, 1, 3, 0])
        assert expected == counts

    def test_split_size4_heat_mix(self, get_visitor):
        file = "test_cases/split/size4_heat_mix.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([0, 0, 1, 0, 3, 4, 12, 1, 2, 3, 0])
        assert expected == counts

    def test_split_size2_detect_SIMD(self, get_visitor):
        file = "test_cases/split/size2_detect_simd.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([0, 0, 1, 2, 2, 2, 7, 0, 1, 1, 0])
        assert expected == counts

    def test_split_size4_detect_SIMD(self, get_visitor):
        file = "test_cases/split/size4_detect_simd.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([0, 0, 1, 4, 2, 4, 13, 0, 1, 3, 0])
        assert expected == counts

    def test_split_size8_detect_SIMD(self, get_visitor):
        file = "test_cases/split/size8_detect_simd.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([0, 0, 1, 8, 2, 8, 25, 0, 1, 7, 0])
        assert expected == counts

    def test_split_size2_heat_SIMD(self, get_visitor):
        file = "test_cases/split/size2_heat_simd.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([0, 0, 1, 0, 2, 2, 7, 2, 1, 1, 0])
        assert expected == counts

    def test_split_size4_heat_SIMD(self, get_visitor):
        file = "test_cases/split/size4_heat_simd.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([0, 0, 1, 0, 2, 4, 13, 4, 1, 3, 0])
        assert expected == counts

    def test_split_size8_heat_SIMD(self, get_visitor):
        file = "test_cases/split/size8_heat_simd.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([0, 0, 1, 0, 2, 8, 25, 8, 1, 7, 0])
        assert expected == counts

    def test_split_size2_mix_x_and_y_SIMD(self, get_visitor):
        file = "test_cases/split/size2_mix_x_and_y_simd.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([0, 0, 1, 0, 4, 2, 12, 0, 4, 2, 0])
        assert expected == counts

    def test_split_size4_mix_x_and_y_SIMD(self, get_visitor):
        file = "test_cases/split/size4_mix_x_and_y_simd.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([0, 0, 1, 0, 4, 4, 22, 0, 6, 6, 0])
        assert expected == counts

    def test_split_size8_mix_x_and_y_SIMD(self, get_visitor):
        file = "test_cases/split/size8_mix_x_and_y_simd.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([0, 0, 1, 0, 4, 8, 42, 0, 10, 14, 0])
        assert expected == counts

    #begin exisitng assay tests
    def test_pcr(self, get_visitor):
        file = "test_cases/assays/pcr.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([2, 4, 3, 1, 1, 1, 7, 3, 0, 0, 3])
        assert expected == counts

    def test_prob_pcr(self, get_visitor):
        file = "test_cases/assays/probabilistic_pcr.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([4, 9, 6, 1, 2, 2, 15, 6, 1, 0, 7])
        assert expected == counts

    def test_pcr_droplet_replenishment(self, get_visitor):
        file = "test_cases/assays/pcr_droplet_replenishment.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([4, 8, 5, 1, 4, 1, 17, 5, 3, 0, 6])
        assert expected == counts

    def test_broad_spectrum_opiate(self, get_visitor):
        file = "test_cases/assays/broad_spectrum_opiate.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([0, 0, 1, 5, 10, 5, 20, 0, 5, 0, 0])
        assert expected == counts

    def test_ciprofloxacin(self, get_visitor):
        file = "test_cases/assays/ciprofloxacin.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([2, 0, 3, 1, 9, 4, 17, 2, 5, 0, 3])
        assert expected == counts

    def test_diazepam(self, get_visitor):
        file = "test_cases/assays/diazepam.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([4, 0, 5, 1, 12, 5, 23, 3, 7, 0, 6])
        assert expected == counts

    def test_dilution(self, get_visitor):
        file = "test_cases/assays/dilution.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([0, 0, 1, 0, 6, 6, 21, 0, 5, 5, 0])
        assert expected == counts

    def test_fentanyl(self, get_visitor):
        file = "test_cases/assays/fentanyl.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([2, 2, 3, 1, 6, 3, 16, 2, 5, 0, 3])
        assert expected == counts

    def test_full_morphine(self, get_visitor):
        file = "test_cases/assays/full_morphine.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([2, 0, 3, 3, 24, 9, 48, 6, 15, 0, 3])
        assert expected == counts

    def test_glucose_detection(self, get_visitor):
        file = "test_cases/assays/glucose_detection.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([0, 0, 1, 5, 20, 10, 35, 0, 10, 0, 0])
        assert expected == counts

    def test_heroin(self, get_visitor):
        file = "test_cases/assays/heroin.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([2, 0, 3, 1, 8, 3, 16, 2, 5, 0, 3])
        assert expected == counts

    def test_image_probe_synthesis(self, get_visitor):
        file = "test_cases/assays/image_probe_synthesis.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([0, 0, 1, 0, 4, 1, 13, 6, 3, 0, 0])
        assert expected == counts

    def test_morphine(self, get_visitor):
        file = "test_cases/assays/morphine.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([2, 0, 3, 1, 9, 4, 17, 2, 5, 0, 3])
        assert expected == counts

    def test_oxycodone(self, get_visitor):
        file = "test_cases/assays/oxycodone.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([2, 0, 3, 1, 8, 3, 16, 2, 5, 0, 3])
        assert expected == counts

    #begin new control assasy tests
    def test_if_else_with_live_droplet_passing(self, get_visitor):
        file = "test_cases/control/if_else_with_live_droplet_passing.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([3, 9, 4, 1, 3, 2, 12, 1, 2, 0, 4])
        assert expected == counts

    def test_if_else_with_halting(self, get_visitor):
        file = "test_cases/control/if_else_with_halting.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([2, 5, 4, 1, 3, 2, 10, 1, 2, 0, 3])
        assert expected == counts

    def test_nested_repeat(self, get_visitor):
        file = "test_cases/control/nested_repeat.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([3, 6, 4, 1, 1, 1, 9, 4, 0, 0, 5])
        assert expected == counts

    def test_repeat_repeat_if_else(self, get_visitor):
        file = "test_cases/control/repeat_repeat_if_else.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([6, 12, 7, 1, 2, 1, 15, 5, 1, 0, 9])
        assert expected == counts

    def test_repeat_repeat_if(self, get_visitor):
        file = "test_cases/control/repeat_repeat_if.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([5, 10, 6, 1, 2, 1, 13, 4, 1, 0, 8])
        assert expected == counts


    def test_repeat_nested_if_else_with_dag6(self, get_visitor):
        file = "test_cases/control/repeat_nested_if_else_with_dag6.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([5, 10, 6, 1, 2, 1, 13, 4, 1, 0, 7])
        assert expected == counts

    def test_repeat_nested_if_else_without_dag6(self, get_visitor):
        file = "test_cases/control/repeat_nested_if_else_without_dag6.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([4, 8, 5, 1, 2, 1, 11, 3, 1, 0, 7])
        assert expected == counts

    def test_repeat_nested_if_with_dag6(self, get_visitor):
        file = "test_cases/control/repeat_nested_if_with_dag6.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([4, 8, 5, 1, 2, 1, 11, 3, 1, 0, 6])
        assert expected == counts

    def test_repeat_nested_if_without_dag6(self, get_visitor):
        file = "test_cases/control/repeat_nested_if_without_dag6.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([3, 6, 4, 1, 2, 1, 9, 2, 1, 0, 6])
        assert expected == counts

    def test_repeat_nested_if_else_without_dag3(self, get_visitor):
        file = "test_cases/control/repeat_nested_if_else_without_dag3.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([4, 8, 5, 1, 2, 1, 11, 3, 1, 0, 7])
        assert expected == counts

    def test_repeat_nested_if_without_dag3(self, get_visitor):
        file = "test_cases/control/repeat_nested_if_without_dag3.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([3, 6, 4, 1, 2, 1, 9, 2, 1, 0, 6])
        assert expected == counts

    def test_repeat_nested_if_else_without_dag3_dag6(self, get_visitor):
        file = "test_cases/control/repeat_nested_if_else_without_dag3_dag6.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([3, 6, 4, 1, 2, 1, 9, 2, 1, 0, 8])
        assert expected == counts

    def test_repeat_nested_if_without_dag3_dag6(self, get_visitor):
        file = "test_cases/control/repeat_nested_if_without_dag3_dag6.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([2, 4, 3, 1, 2, 1, 7, 1, 1, 0, 3])
        assert expected == counts

    # begin complex repeat if else
    def test_complex_repeat_if_else_all(self, get_visitor):
        file = "test_cases/control/complex_repeat_if_else_all.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([8, 16, 9, 1, 2, 1, 19, 7, 1, 0, 11])
        assert expected == counts

    def test_complex_repeat_if_else_no_dag5(self, get_visitor):
        file = "test_cases/control/complex_repeat_if_else_no_dag5.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([7, 14, 8, 1, 2, 1, 17, 6, 1, 0, 10])
        assert expected == counts

    def test_complex_repeat_if_else_no_dag3_dag5(self, get_visitor):
        file = "test_cases/control/complex_repeat_if_else_no_dag3_dag5.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([6, 12, 7, 1, 2, 1, 15, 5, 1, 0, 11])
        assert expected == counts

    def test_complex_repeat_if_else_no_dag3_dag5_dag6(self, get_visitor):
        file = "test_cases/control/complex_repeat_if_else_no_dag3_dag5_dag6.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([5, 10, 6, 1, 2, 1, 13, 4, 1, 0, 13])
        assert expected == counts

    # begin deep nested repeats
    # size 3
    def test_deep_nested_repeats_size_3_all(self, get_visitor):
        file = "test_cases/control/deep_nested_repeats_size_3_all.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([4, 8, 5, 1, 2, 1, 11, 3, 1, 0, 7])
        assert expected == counts

    def test_deep_nested_repeats_size_3_dag3_only(self, get_visitor):
        file = "test_cases/control/deep_nested_repeats_size_3_dag3_only.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([2, 4, 3, 1, 2, 1, 7, 1, 1, 0, 3])
        assert expected == counts

    def test_deep_nested_repeats_size_3_dag5_only(self, get_visitor):
        file = "test_cases/control/deep_nested_repeats_size_3_dag5_only.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([2, 4, 3, 1, 2, 1, 7, 1, 1, 0, 3])
        assert expected == counts

    def test_deep_nested_repeats_size_3_dag7_only(self, get_visitor):
        file = "test_cases/control/deep_nested_repeats_size_3_dag7_only.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([2, 4, 3, 1, 2, 1, 7, 1, 1, 0, 3])
        assert expected == counts

    def test_deep_nested_repeats_size_3_no_dag3(self, get_visitor):
        file = "test_cases/control/deep_nested_repeats_size_3_no_dag3.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([3, 6, 4, 1, 2, 1, 9, 2, 1, 0, 5])
        assert expected == counts

    def test_deep_nested_repeats_size_3_no_dag5(self, get_visitor):
        file = "test_cases/control/deep_nested_repeats_size_3_no_dag5.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([3, 6, 4, 1, 2, 1, 9, 2, 1, 0, 5])
        assert expected == counts

    def test_deep_nested_repeats_size_3_no_dag7(self, get_visitor):
        file = "test_cases/control/deep_nested_repeats_size_3_no_dag7.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([3, 6, 4, 1, 2, 1, 9, 2, 1, 0, 5])
        assert expected == counts

    # deep repeat size 4
    def test_deep_nested_repeats_size_4_all(self, get_visitor):
        file = "test_cases/control/deep_nested_repeats_size_4_all.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([5, 10, 6, 1, 2, 1, 13, 4, 1, 0, 9])
        assert expected == counts

    def test_deep_nested_repeats_size_4_dag3(self, get_visitor):
        file = "test_cases/control/deep_nested_repeats_size_4_dag3_only.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([2, 4, 3, 1, 2, 1, 7, 1, 1, 0, 3])
        assert expected == counts

    def test_deep_nested_repeats_size_4_dag5(self, get_visitor):
        file = "test_cases/control/deep_nested_repeats_size_4_dag5_only.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([2, 4, 3, 1, 2, 1, 7, 1, 1, 0, 3])
        assert expected == counts

    def test_deep_nested_repeats_size_4_dag7(self, get_visitor):
        file = "test_cases/control/deep_nested_repeats_size_4_dag7_only.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([2, 4, 3, 1, 2, 1, 7, 1, 1, 0, 3])
        assert expected == counts

    def test_deep_nested_repeats_size_4_dag9(self, get_visitor):
        file = "test_cases/control/deep_nested_repeats_size_4_dag9_only.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([2, 4, 3, 1, 2, 1, 7, 1, 1, 0, 3])
        assert expected == counts

    def test_deep_nested_repeats_size_4_no_dag3(self, get_visitor):
        file = "test_cases/control/deep_nested_repeats_size_4_no_dag3.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([4, 8, 5, 1, 2, 1, 11, 3, 1, 0, 7])
        assert expected == counts

    def test_deep_nested_repeats_size_4_no_dag3_dag5(self, get_visitor):
        file = "test_cases/control/deep_nested_repeats_size_4_no_dag3_dag5.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([3, 6, 4, 1, 2, 1, 9, 2, 1, 0, 5])
        assert expected == counts

    def test_deep_nested_repeats_size_4_no_dag3_dag7(self, get_visitor):
        file = "test_cases/control/deep_nested_repeats_size_4_no_dag3_dag7.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([3, 6, 4, 1, 2, 1, 9, 2, 1, 0, 5])
        assert expected == counts

    def test_deep_nested_repeats_size_4_no_dag3_dag9(self, get_visitor):
        file = "test_cases/control/deep_nested_repeats_size_4_no_dag3_dag9.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([3, 6, 4, 1, 2, 1, 9, 2, 1, 0, 5])
        assert expected == counts

    def test_deep_nested_repeats_size_4_no_dag5(self, get_visitor):
        file = "test_cases/control/deep_nested_repeats_size_4_no_dag5.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([4, 8, 5, 1, 2, 1, 11, 3, 1, 0, 7])
        assert expected == counts

    def test_deep_nested_repeats_size_4_no_dag5_dag7(self, get_visitor):
        file = "test_cases/control/deep_nested_repeats_size_4_no_dag5_dag7.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([3, 6, 4, 1, 2, 1, 9, 2, 1, 0, 5])
        assert expected == counts

    def test_deep_nested_repeats_size_4_no_dag5_dag9(self, get_visitor):
        file = "test_cases/control/deep_nested_repeats_size_4_no_dag5_dag9.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([3, 6, 4, 1, 2, 1, 9, 2, 1, 0, 5])
        assert expected == counts

    def test_deep_nested_repeats_size_4_no_dag7(self, get_visitor):
        file = "test_cases/control/deep_nested_repeats_size_4_no_dag7.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([4, 8, 5, 1, 2, 1, 11, 3, 1, 0, 7])
        assert expected == counts

    def test_deep_nested_repeats_size_4_no_dag7_dag9(self, get_visitor):
        file = "test_cases/control/deep_nested_repeats_size_4_no_dag7_dag9.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([3, 6, 4, 1, 2, 1, 9, 2, 1, 0, 5])
        assert expected == counts

    def test_deep_nested_repeats_size_4_no_dag9(self, get_visitor):
        file = "test_cases/control/deep_nested_repeats_size_4_no_dag9.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([4, 8, 5, 1, 2, 1, 11, 3, 1, 0, 7])
        assert expected == counts

    # deep repeat size 5
    def test_deep_nested_repeats_size_5_all(self, get_visitor):
        file = "test_cases/control/deep_nested_repeats_size_5_all.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([6, 12, 7, 1, 2, 1, 15, 5, 1, 0, 11])
        assert expected == counts

    def test_deep_nested_repeats_size_5_no_dag7_dag11(self, get_visitor):
        file = "test_cases/control/deep_nested_repeats_size_5_no_dag7_dag11.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([4, 8, 5, 1, 2, 1, 11, 3, 1, 0, 7])
        assert expected == counts

    #begin while
    def test_simple_while(self, get_visitor):
        file = "test_cases/control/simple_while.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([2, 4, 3, 1, 2, 1, 7, 1, 1, 0, 4])
        assert expected == counts

    def test_while_while_all(self, get_visitor):
        file = "test_cases/control/while_while_all.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([4, 8, 5, 1, 2, 1, 11, 3, 1, 0, 8])
        assert expected == counts

    def test_while_while_no_dag3(self, get_visitor):
        file = "test_cases/control/while_while_no_dag3.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([3, 6, 4, 1, 2, 1, 9, 2, 1, 0, 8])
        assert expected == counts

    def test_while_while_no_dag6(self, get_visitor):
        file = "test_cases/control/while_while_no_dag6.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([3, 6, 4, 1, 2, 1, 9, 2, 1, 0, 8])
        assert expected == counts

    def test_three_whiles(self, get_visitor):
        file = "test_cases/control/three_whiles.bs"
        counts = self.get_compiled_mfsim(get_visitor(file), file)

        expected = str([6, 12, 7, 1, 2, 1, 15, 5, 1, 0, 12])
        assert expected == counts


# [num_cgs, num_transfers, num_dags, num_detects,
#                 num_dispense, num_dispose, num_edges, num_heats,
#                 num_mixes, num_splits, num_exps]