from ggplot import ggplot, aes, geom_point, geom_line, theme_bw
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import CBunch
import CSignal
from importlib import reload

matplotlib.rcParams["figure.figsize"] = "100, 100"

b1 = CBunch.Bunch()
at = np.arange(0,1500, .75*np.pi/b1.Synch["wFreq"])
#at = np.linspace(0,2000, 1e3)

s1 = CSignal.Signal(b1, at)

s1.addNoise(3e-2)
ggplot(s1.Signal, aes()) + \
    geom_line(aes(x="Time", y="Val"), color="red", size=.05) + \
    geom_point(aes(x="Time",y="ValNs"), col="blue") + \
    theme_bw()

#f = lambda t, l,w,p: 1e3*np.exp(l*t)*np.sin(w*t + p)
#s1.fit(f, [-1e-4, s1.Bunch.Synch["wFreq"], 0])

#s1.Spectrum()
#plt.figure(figsize=(20,20))
#plt.semilogy(s1.PSD.wFreq, s1.PSD.Pow)

s1.findPts()

ggplot(s1.Signal, aes()) + \
    geom_line(aes(x="Time", y="Val"), color="gray", size=.5) + \
    geom_point(aes(x="Time",y="Val"), data=s1.specPts, col="blue") +\
    theme_bw()
