import pandas
import numpy as np
import pathos.multiprocessing as mp
from scipy.optimize import curve_fit
from scipy.signal import welch

class Signal:
    """Contains fields and methods of a signal
    
    A signal is a property of a bunch. 
    """
    
    Bunch=None
    Signal=None
    specPts=None
    Model=None
    PSD=None
    __NSmpl=None
    
    def __init__(self, bunch, smpl_pts):
        self.Bunch = bunch
        self.Signal = self.Bunch.project(smpl_pts)
        self._NSmpl = 1
        
    def split(self):
        pass
    
    def sample(self, at):
        pass
    
    def addNoise(self, rerr):
        self.Signal = self.Signal.assign(Noise = self.Signal.Val*np.random.normal(0, rerr, len(self.Signal)))
        self.Signal = self.Signal.assign(ValNs = self.Signal.Val+self.Signal.Noise)
        
    def fit(self, FUN, Guess):
        self.Model = curve_fit(FUN, self.Signal.Time, self.Signal.ValNs, p0=Guess)
        return {"Estimate" : self.Model[0], "SE" : np.sqrt(np.diag(self.Model[1]))}
        
    def Spectrum(self):
        fs = 1/(self.Signal.Time[2] - self.Signal.Time[1])
        psd = welch(self.Signal.ValNs, fs)
        self.PSD = pandas.DataFrame({
            "Freq": psd[0],
            "Pow" : psd[1]
        })
        self.PSD = self.PSD.assign(wFreq = self.PSD.Freq*2*np.pi)

    def findPts(self, what="Node", wguess=None):
        
        switch = lambda x: {"Node": 1, "Envelope": -1}.get(x, 1)
        
        k = switch(what) #this'll determine the direction of optimization
        tgt = lambda x: k*self.Bunch._polProj(x)**2
        def finder(sub, fn):
            from scipy.optimize import minimize
            x0 = sub.Time.data[0]
            dx = np.pi/self.Bunch.Synch["wFreq"]/2
            bnd = (x0-dx, x0+dx)
            x0 = minimize(fn, x0, bounds=((bnd[0], bnd[1]),), tol=1e-9).x
            sub['Time'] = x0.data[0]
            sub['Which'] = "Optim"
            return sub
      
        pts0 = self._NullSpecPts(what, wguess)
        pts0_g = pts0.groupby(list(range(len(pts0))))
        
        pool = mp.ProcessingPool(processes=mp.cpu_count())
        
        #pts1 = pandas.concat([finder(group) for name,group in pts0_g])
        pts1 = pandas.concat(pool.map(finder, [group for name,group in pts0_g], [tgt]*len(pts0)))
        
        pool.close()
        pool.join()
        
        pts1['Val'] = self.Bunch._polProj(pts1['Time'])
      
        self.specPts = pandas.concat([pts0, pts1]).sort_values("Time")
        
    def _NullSpecPts(self, what="Node", wref=None):
        if wref is not None:
            w0 = wref 
        else: 
            w0 = self.Bunch.Synch["wFreq"]
        
        p0 = self.Bunch.Synch["Phi"]
        
        _dum = lambda Time: int(np.floor((w0*Time+p0-np.pi/2)/2/np.pi))
      
        Nstt = _dum(self.Signal.Time[0])
        Ntot = _dum(self.Signal.Time[len(self.Signal)-1])
      
        switch = lambda x: {"Node": 0, "Envelope": np.pi/2}.get(x, 0)
      
        d = switch(what)
        tnu = [(2*np.pi*x -p0+d)/w0  for x in range(Nstt,Ntot+1)]
        tnu = [x for x in tnu if not x < 0]
        tnd = [x+np.pi/w0 for x in tnu]
      
        df1 = pandas.DataFrame({
            "N" : list(range(1,len(tnu)+1)) + list(range(1,len(tnd)+1)),
            "Side": ["U"]*len(tnu)+ ["D"]*len(tnd),
            "Which": "Null"
        })
        
        return pandas.concat([df1, self.Bunch.project(tnu+tnd)], axis=1)
