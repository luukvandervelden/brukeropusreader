import numpy as np
from scipy.interpolate import interp1d


class OpusData(dict):
    def get_range(self, spec_name="AB", wavenums=True):
        '''Get the wavelength, by reading the lower (LXV) and
        upper (FXV) limit and interpolating the values, based on the reported
        number of datapoints (NPT)
        '''
        param_key = f"{spec_name} Data Parameter"
        fxv = self[param_key]["FXV"]
        lxv = self[param_key]["LXV"]
        # the number of points here is OK. It is "AB" that can return more values (equals to zero)
        npt = self[param_key]["NPT"]
        x_no_unit = np.linspace(fxv, lxv, npt)
        if wavenums:
            return x_no_unit
        else:
            return 10_000_000 / x_no_unit

    def interpolate(self, start, stop, num, spec_name="AB"):
        xav = self.get_range(spec_name=spec_name)
        yav = self[spec_name]
        iwave_nums = np.linspace(start, stop, num)
        f2 = interp1d(xav, yav, kind="cubic", fill_value="extrapolate")
        return iwave_nums, f2(iwave_nums)

    def get_spectra(self, spec_name="AB"):
        '''Get the spectra series. The first spectrum is at index 8 and the length
        is 1659 data points, so it goes from 8 to 1666. The second starts at 1705.
        '''
        # TODO: 405 spectra could be different, I should extract that number
        # from the file
        spectra = np.empty(shape=(405, 1659))
        for i in range(0,405):
            indices = np.arange(8,1667) + i*(1659 + 39 - 1)
            spectra[i] = self[spec_name][indices]

        return spectra
