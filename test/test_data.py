"""Test data class.

Created on Mon Apr  4 16:36:41 2016

@author: patricia
"""
import pytest
import numpy as np
from idtxl.data import Data
import idtxl.idtxl_utils as utils


def test_data_properties():

    n = 10
    d = Data(np.arange(n), 's', normalise=False)
    real_time = d.n_realisations_samples()
    assert (real_time == n), 'Realisations in time are not returned correctly.'
    cv = (0, 8)
    real_time = d.n_realisations_samples(current_value=cv)
    assert (real_time == (n - cv[1])), ('Realisations in time are not '
                                        'returned correctly when current value'
                                        ' is set.')


def test_set_data():
    """Test if data is written correctly into a Data instance."""
    source = np.expand_dims(np.repeat(1, 30), axis=1)
    target = np.expand_dims(np.arange(30), axis=1)

    data = Data(normalise=False)
    data.set_data(np.vstack((source.T, target.T)), 'ps')

    assert (data.data[0, :].T == source.T).all(), ('Class data does not match '
                                                   'input (source).')
    assert (data.data[1, :].T == target.T).all(), ('Class data does not match '
                                                   'input (target).')

    d = Data()
    dat = np.arange(10000).reshape((2, 1000, 5))  # random data with correct
    d = Data(dat, dim_order='psr')               # order od dimensions
    assert (d.data.shape[0] == 2), ('Class data does not match input, number '
                                    'of processes wrong.')
    assert (d.data.shape[1] == 1000), ('Class data does not match input, '
                                       'number of samples wrong.')
    assert (d.data.shape[2] == 5), ('Class data does not match input, number '
                                    'of replications wrong.')
    dat = np.arange(3000).reshape((3, 1000))  # random data with incorrect
    d = Data(dat, dim_order='ps')            # order of dimensions
    assert (d.data.shape[0] == 3), ('Class data does not match input, number '
                                    'of processes wrong.')
    assert (d.data.shape[1] == 1000), ('Class data does not match input, '
                                       'number of samples wrong.')
    assert (d.data.shape[2] == 1), ('Class data does not match input, number '
                                    'of replications wrong.')
    dat = np.arange(5000)
    d.set_data(dat, 's')
    assert (d.data.shape[0] == 1), ('Class data does not match input, number '
                                    'of processes wrong.')
    assert (d.data.shape[1] == 5000), ('Class data does not match input, '
                                       'number of samples wrong.')
    assert (d.data.shape[2] == 1), ('Class data does not match input, number '
                                    'of replications wrong.')


def test_data_normalisation():
    """Test if data are normalised correctly when stored in a Data instance."""
    a_1 = 100
    a_2 = 1000
    source = np.random.randint(a_1, size=1000)
    target = np.random.randint(a_2, size=1000)

    data = Data(normalise=True)
    data.set_data(np.vstack((source.T, target.T)), 'ps')

    source_std = utils.standardise(source)
    target_std = utils.standardise(target)
    assert (source_std == data.data[0, :, 0]).all(), ('Standardising the '
                                                      'source did not work.')
    assert (target_std == data.data[1, :, 0]).all(), ('Standardising the '
                                                      'target did not work.')


def test_get_realisations():
    """Test low-level function for data retrieval."""
    dat = Data()
    dat.generate_mute_data()
    idx_list = [(0, 4), (0, 6)]
    current_value = (0, 3)
    with pytest.raises(RuntimeError):
        dat.get_realisations(current_value, idx_list)

    # Test retrieved data for one/two replications in time (i.e., the current
    # value is equal to the last sample)
    n = 7
    d = Data(np.arange(n + 1), 's', normalise=False)
    current_value = (0, n)
    dat = d.get_realisations(current_value, [(0, 1)])[0]
    assert (dat[0][0] == 1)
    assert (dat.shape == (1, 1))
    d = Data(np.arange(n + 2), 's', normalise=False)
    current_value = (0, n)
    dat = d.get_realisations(current_value, [(0, 1)])[0]
    assert (dat[0][0] == 1)
    assert (dat[1][0] == 2)
    assert (dat.shape == (2, 1))

    # Test retrieval of realisations of the current value.
    n = 7
    d = Data(np.arange(n), 's', normalise=False)
    current_value = (0, n)
    dat = d.get_realisations(current_value, [current_value])[0]


def test_permute_replications():
    """Test surrogate creation by permuting replications."""
    n = 20
    data = Data(np.vstack((np.zeros(n),
                           np.ones(n) * 1,
                           np.ones(n) * 2,
                           np.ones(n) * 3)).astype(int),
                         'rs',
                         normalise=False)
    current_value = (0, n)
    l = [(0, 1), (0, 3), (0, 7)]
    [perm, perm_idx] = data.permute_replications(current_value=current_value,
                                                 idx_list=l)
    assert (np.all(perm[:, 0] == perm_idx)), 'Permutation did not work.'

    # Assert that samples have been swapped within the permutation range for
    # the first replication.
    rng = 3
    current_value = (0, 3)
    l = [(0, 0), (0, 1), (0, 2)]
    # data = Data(np.arange(n), 's', normalise=False)
    data = Data(np.vstack((np.arange(n),
                           np.arange(n))).astype(int),
                'rs',
                normalise=False)
    perm_opts = {
        'perm_type': 'local',
        'perm_range': rng
    }
    [perm, perm_idx] = data.permute_samples(current_value=current_value,
                                            idx_list=l,
                                            perm_opts=perm_opts)
    samples = np.arange(rng)
    i = 0
    n_per_repl = int(data.n_realisations(current_value) / data.n_replications)
    for p in range(n_per_repl // rng):
        assert (np.unique(perm[i:i + rng, 0]) == samples).all(), ('The '
            'permutation range was not respected.')
        samples += rng
        i += rng
    rem = n_per_repl % rng
    if rem > 0:
        assert (np.unique(perm[i:i + rem, 0]) == samples[0:rem]).all(), ('The '
            'remainder did not contain the same realisations.')

    # Test assertions that perm_range is not too low or too high.
    perm_opts = {
        'perm_type': 'local',
        'perm_range': 1
    }
    with pytest.raises(AssertionError):
        data.permute_samples(current_value=current_value,
                             idx_list=l,
                             perm_opts=perm_opts)
    perm_opts['perm_range'] = np.inf
    with pytest.raises(AssertionError):
        data.permute_samples(current_value=current_value,
                             idx_list=l,
                             perm_opts=perm_opts)
    # Test ValueError if a string other than 'max' is given for perm_range.
    perm_opts['perm_range'] = 'foo'
    with pytest.raises(ValueError):
        data.permute_samples(current_value=current_value,
                             idx_list=l,
                             perm_opts=perm_opts)

def test_permute_samples():
    pass

def test_get_data_slice():
    n = 10
    n_replications = 3
    d = Data(np.vstack((np.zeros(n), np.ones(n), 2 * np.ones(n))),
             'rs', normalise=False)
    [s, i] =  d._get_data_slice(process=0, offset_samples=0, shuffle=False)

    # test unshuffled slicing
    for r in range(n_replications):
        assert s[r][0] == i[r], 'Replication index {0} is not correct.'.format(
                                                                            r)
    # test shuffled slicing
    [s, i] = d._get_data_slice(process=0, offset_samples=0, shuffle=True)
    for r in range(n_replications):
        assert s[r][0] == i[r], 'Replication index {0} is not correct.'.format(
                                                                            r)

    offset = 3
    d = Data(np.arange(n), 's', normalise=False)
    [s, i] =  d._get_data_slice(process=0, offset_samples=offset,
                                shuffle=False)
    assert s.shape[1] == (n - offset), 'Offset not handled correctly.'


def test_create_surrogates():
    pass


def test_swap_blocks():
    """Test block-wise swapping of samples."""
    d = Data()
    d.generate_mute_data()

    # block_size divides the length of the data to be permuted, swap_range
    # leads to 2 remaining blocks
    n = 50
    block_size = 5
    swap_range = 4
    perm = d._swap_blocks(n, block_size, swap_range)
    assert sum(perm == 0) == block_size, 'Incorrect block size.'
    assert perm.shape[0] == n, 'Incorrect length of permuted indices.'

    # block_size leads to one block of length 1, swap_range divides the no.
    # blocks
    n = 50
    block_size = 7
    swap_range = 4
    perm = d._swap_blocks(n, block_size, swap_range)
    assert sum(perm == 0) == block_size, 'Incorrect block size.'
    assert perm.shape[0] == n, 'Incorrect length of permuted indices.'
    n_blocks = np.ceil(n/7).astype(int)
    assert n_blocks == 8, 'No. blocks is incorrect.'
    assert sum(perm == n_blocks - 1) == 1, ('No. remaining samples in the last'
                                            ' block is incorrect.')

    # no remaining samples or blocks
    n = 30
    block_size = 5
    swap_range = 3
    perm = d._swap_blocks(n, block_size, swap_range)
    assert sum(perm == 0) == block_size, 'Incorrect block size.'
    assert perm.shape[0] == n, 'Incorrect length of permuted indices.'


def test_circular_shift():
    """Test circular shifting of samples."""
    d = Data()
    d.generate_mute_data()
    n = 20
    max_shift = 10
    [perm, shift] = d._circular_shift(n, max_shift)
    assert perm[0] == (n - shift), 'First index after circular shift is wrong!'
    assert shift <= max_shift, 'Actual shift exceeded max_shift.'
    assert perm.shape[0] == n, 'Incorrect length of permuted indices.'


def test_swap_local():
    pass


if __name__ == '__main__':
    test_swap_blocks()
    test_circular_shift()
    test_swap_local()
    test_create_surrogates()
    test_get_data_slice()
    test_get_realisations()
    test_data_normalisation()
    test_set_data()
    test_permute_replications()
    test_data_properties()
