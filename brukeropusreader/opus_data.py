import numpy as np
from scipy.interpolate import interp1d
from brukeropusreader.constants import JUNK_LINES_START, JUNK_LINES_BETWEEN

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
        '''Get the spectra series. The first spectrum starts after a number of
        junk lines 'JUNK_LINES_START'. There is 'JUNK_LINES_BETWEEN'
        lines between the spectra.
        '''
        data = self[spec_name]
        npt = self[f"{spec_name} Data Parameter"]["NPT"]
        num_spectra = round(
            (data.size - JUNK_LINES_START) / (npt + JUNK_LINES_BETWEEN))

        spectra = np.empty(shape=(num_spectra, npt))
        for i in range(0,num_spectra):
            start = JUNK_LINES_START + i*(npt + JUNK_LINES_BETWEEN)
            spectra[i] = data[start:start+npt]

        return spectra
