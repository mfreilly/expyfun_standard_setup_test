# -*- coding: utf-8 -*-

from os import path as op
import numpy as np
from expyfun import (ExperimentController, visual, assert_version,
                     get_keyboard_input, decimals_to_binary)
from expyfun.io import read_hdf5, read_wav

feedback = False  # should be False for MEG
assert_version('9c4bcea')
p = read_hdf5(op.join(op.dirname(__file__), 'params.hdf5'))
stim_dir = op.join(op.dirname(__file__), p['stim_dir'])

bg_color = [0.2] * 3
fix_color = [0.5] * 3
v_off = 2.


with ExperimentController('standard_setup', full_screen=False,
                          stim_db=75, noise_db=45,
                          participant='s', session='0', output_dir=None,
                          suppress_resamp=True, check_rms=None, version='9c4bcea') as ec:
    square = visual.Rectangle(ec, [0, 0, 10, 10], units='deg')
    ec.screen_text('expy_standard_setup_test.', wrap=False)    
    ec.set_background_color(bg_color)
    fix = visual.FixationDot(ec, colors=[fix_color, bg_color])
    circ = visual.Circle(ec, radius=1, units='deg', line_color=fix_color,
                         fill_color=None)
    strs = ',   '.join(token.capitalize() for token in p['tokens'])
    targ_text = visual.Text(ec, strs, pos=[0, v_off],
                            units='deg', color=fix_color)

    # actual experiment
    ec.set_visible(False)
    bi = get_keyboard_input('Enter block number (%s): ' % 1, 1, int) - 1
    session = int(ec.session) - 1 if ec.session != '' else 0
    while 0 <= bi < len(p['block_trials']):
        # start of each block
        ec.start_noise()
        ec.set_visible(True)
        ec.write_data_line('block', bi)
        fix.draw()
        ec.flip()
        ec.wait_for_presses(5.0)

        # each trial
        trials = p['block_trials'][p['blocks'][session][bi]]
        for ti in trials:
            # stimulus
            samples = read_wav(op.join(stim_dir, p['stim_names'][ti]))[0]
            ec.load_buffer(samples)
            stamp = np.concatenate([p['cond_mat'][ti], p['which_targ'][ti]])
            id_ = decimals_to_binary(stamp, [1, 2, 2, 1, 2, 2])
            ec.identify_trial(ec_id=id_, ttl_id=id_)
            ec.listen_presses()

            fix.draw()
            t0 = ec.start_stimulus()

            # response
            fix.draw()
            circ.draw()
            targ_text.draw()
            ec.flip(t0 + p['resp_onset'])
            ec.stamp_triggers([2])
            ec.stop()
            ec.trial_ok()
            ec.wait_one_press()
            fix.draw()
            ec.flip()

            # feedback
            if feedback:
                txt = 'Answer: %s' % ', '.join(p['tokens'][pp] 
                                               for pp in p['which_targ'][ti])
                visual.Text(ec, txt, [0, v_off], fix_color,
                            units='deg').draw()
                fix.draw()
                ec.screen_prompt('Press a button to continue', pos=[0, -v_off],
                                 units='deg', clear_after=False, wrap=False,
                                 color=fix_color)
                fix.draw()
                ec.flip()
            ec.wait_secs(p['inter_trial_dur'])

        # end of each block
        ec.stop_noise()
        ec.set_visible(False)
        bi = get_keyboard_input('Enter block number ({0}): '.format(bi + 2),
                                bi + 2, int) - 1
