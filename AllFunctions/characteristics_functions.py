import numpy as np
import scipy.integrate as integrate
import scipy.stats as st
import scipy.special as sp
import enum
import scipy.optimize as optimize
from scipy.optimize import minimize

def ChFHestonModel(r, tau, kappa, gamma, vbar, v0, rho):
    i = complex(0.0, 1.0)
    D1 = lambda u: np.sqrt(np.power(kappa-gamma*rho*i*u, 2)+(u**2 + i*u) * gamma**2)
    g  = lambda u: (kappa-gamma*rho*i*u-D1(u))/(kappa-gamma*rho*i*u + D1(u))
    C  = lambda u: (1.0-np.exp(-D1(u)*tau))/(gamma*gamma*(1.0-g(u)*np.exp(-D1(u)*tau)))\
        *(kappa-gamma*rho*i*u-D1(u))
    # Note that we exclude the term -r*tau, as the discounting is performed in the COS method
    A  = lambda u: r * i*u *tau + kappa*vbar*tau/gamma/gamma *(kappa-gamma*rho*i*u-D1(u))\
        - 2*kappa*vbar/gamma/gamma * np.log((1.0-g(u)*np.exp(-D1(u)*tau))/(1.0-g(u)))

    cf = lambda u: np.exp(A(u) + C(u)*v0)
    return cf

def ChFBlackScholes(r, sigma, tau):
    cf = lambda u: np.exp((r - 0.5 * sigma**2)* 1j * u * tau - 0.5 * sigma**2 * u**2 * tau)
    return cf

def ChFBatesModel(r,tau,kappa,gamma,vbar,v0,rho,xiP,muJ,sigmaJ):
    i = complex(0.0,1.0)
    D1 = lambda u: np.sqrt(np.power(kappa-gamma*rho*i*u,2)+(u*u+i*u)*gamma*gamma)
    g  = lambda u: (kappa-gamma*rho*i*u-D1(u))/(kappa-gamma*rho*i*u+D1(u))
    C  = lambda u: (1.0-np.exp(-D1(u)*tau))/(gamma*gamma*(1.0-g(u)*\
                               np.exp(-D1(u)*tau)))*(kappa-gamma*rho*i*u-D1(u))
    # Note that we exclude the term -r*tau, as the discounting is performed in the COS method
    AHes= lambda u: r * i*u *tau + kappa*vbar*tau/gamma/gamma *(kappa-gamma*\
        rho*i*u-D1(u)) - 2*kappa*vbar/gamma/gamma*np.log((1.0-g(u)*np.exp(-D1(u)*tau))/(1.0-g(u)))

    A = lambda u: AHes(u) - xiP * i * u * tau *(np.exp(muJ+0.5*sigmaJ*sigmaJ) - 1.0) + \
            xiP * tau * (np.exp(i*u*muJ - 0.5 * sigmaJ * sigmaJ * u * u) - 1.0)

    cf = lambda u: np.exp(A(u) + C(u)*v0)
    return cf

def EFun(tau, u, e1, e2, k, gamma):
    eFun = ((k - e1) / gamma**2) * (1 - np.exp(-e1*tau))/(1 - e2 * np.exp(-e1*tau))
    return eFun

def CFun(tau, u, c1, c2, kr, gammar):
    cFun = ((kr - c1) / gammar**2) * (1 - np.exp(-c1*tau))/(1 - c2 * np.exp(-c1*tau))
    return cFun

def DFun(tau, u, k, gamma, d1, l1, v0, vb, krho, T):
    dFun = gamma * d1 * ( np.exp(-k*T)*(v0 - vb)/(krho + k) + vb/krho + np.exp(-k*T)*(vb - v0)/(krho + k - l1) - vb/(krho - l1) + \
        (- np.exp(-k*T)*(v0-vb)/(k + krho) - vb/krho + vb/(krho - l1) - np.exp(-k*T)*(vb-v0)/(k + krho - l1) ) )
    return dFun


def AFun(tau, u, muJ, sigmaJ, xip, k, vb, gamma, l1, d1, v0, krho, murho,
                        sigmarho, rho4, rho5, T, kr, gammar, mur, c1, c2, r0):
    i = complex(0, 1)

    ct = lambda t: 1/(4*k) * gamma**2 * (1 - np.exp(-k*t))
    d1 = 4*k*vb/(gamma**2)
    lambda1t = lambda t: (4*k*v0*np.exp(-k*t))/(gamma**2 * (1 - np.exp(-k*t)))

    L1 = lambda t: np.sqrt(ct(t) * (lambda1t(t) - 1) + ct(t)*d1 + (ct(t)*d1)/(2*(d1+lambda1t(t))))

    c2t = lambda t: 1/(4*kr) * gammar**2 * (1 - np.exp(-kr*t))
    d2 = 4*kr*mur/(gammar**2)
    lambda2t = lambda t: (4*kr*r0*np.exp(-kr*t))/(gammar**2 * (1 - np.exp(-kr*t)))

    L2 = lambda t: np.sqrt(c2t(t) * (lambda2t(t) - 1) + c2t(t)*d2 + (c2t(t)*d2)/(2*(d2+lambda2t(t))))

    a = np.sqrt(vb - gamma**2/(8*k))
    b = np.sqrt(v0) - a
    c = - np.log(1/b * (L1(1) - a))
    m = np.sqrt(mur - gammar**2/(8*kr))
    n = np.sqrt(r0) - m
    o = - np.log(1/n * (L2(1) - m))

    I1 = -i*u*(np.exp(muJ+0.5*sigmaJ**2) - 1)*tau*xip + xip*(np.exp(muJ*i*u - 0.5*sigmaJ**2 * u**2) - 1)*tau +\
        k*vb*(k-e1)/gamma**2 * (tau - np.exp(-l1*tau)/(-l1))

    z = np.linspace(0, tau, 100)

    f_I21 = lambda z,u: np.exp(-c*(T-z)) * DFun(z, u, k, gamma, d1, l1, v0, vb, krho, T)
    I21 = integrate.trapz(np.array(list(map(lambda z: f_I21(z, u), z))), z)

    I2 = (krho*murho + sigmarho*rho4*i*u*a) * l1*(krho*(krho - l1)*(v0 - vb) + np.exp(k*T)*(k+krho)*(k+krho-l1)*vb)/(krho**2 * (k+krho)*(krho - l1)*(k+krho-l1)) + ( np.exp(k*(tau-T))*(v0-vb)*tau)/(k+krho) + vb*tau/krho +\
        (np.exp(-l1*tau)*vb*tau)/(l1-krho) + (np.exp(-k*T+k*tau-l1*tau)*(vb-v0)*tau)/(k+krho-l1) +\
        sigmarho*rho4*i*u*b * I21

    f = lambda z, u: DFun(z, u, k, gamma, d1, l1, v0, vb, krho, T)

    I3 = 0.5*sigmarho**2 * integrate.trapz(np.array(list(map(lambda z: (f(z, u))**2, z))), z)

    f_I41 = lambda z,u: CFun(z, u, c1, c2, kr, gammar)
    f_I42 = lambda z,u: np.exp(-o*(T-z)) * CFun(z, u, c1, c2, kr, gammar)
    f_I43 = lambda z,u: np.exp(-c*(T-z)) * CFun(z, u, c1, c2, kr, gammar)
    f_I44 = lambda z,u: np.exp((-o-c)*(T-z)) * CFun(z, u, c1, c2, kr, gammar)

    I41 = integrate.trapz(np.array(list(map(lambda z: f_I41(z, u), z))), z)
    I42 = integrate.trapz(np.array(list(map(lambda z: f_I42(z, u), z))), z)
    I43 = integrate.trapz(np.array(list(map(lambda z: f_I43(z, u), z))), z)
    I44 = integrate.trapz(np.array(list(map(lambda z: f_I44(z, u), z))), z)

    I4 = (kr*mur + gammar*rho5*i*u*m*a) * I41 + gammar*rho5*i*u*a*n* I42 +\
        gammar*rho5*i*u*m*b* I43 + gammar*rho5*i*u*n*b * I44

    return I1 + I2 + I3 + I4

def ChFBates_StochIR_StochCor(tau, T, k, gamma, vb, kr, gammar, mur, krho, murho, sigmarho, rho4, rho5,
                    xip, muJ, sigmaJ, v0, r0, rho0):
    i = complex(0.0, 1.0)

    #define E function
    e1 = lambda u: np.sqrt(k**2 + gamma**2 * (u**2 + i*u))
    e2 = lambda u: (k - e1) / (k + e1)

    eFun = lambda u: EFun(tau, u, e1, e2, k, gamma)

    #define C function
    c1 = lambda u: np.sqrt(kr**2 + gammar**2 * (u**2 + i*u))
    c2 = lambda u: (kr - c1) / (kr + c1)

    cFun = lambda u: CFun(tau, u, c1, c2, kr, gammar)

    #define D function
    d1 = lambda u: i*u * (k - e1)/gamma**2
    l1 = lambda u: -np.log( (np.exp(-e1) - e2*np.exp(-e1))/(1 - e2*np.exp(-e1)) )
    dFun = lambda u: DFun(tau, u, k, gamma, d1, l1, v0, vb, krho, T)

    aFun = lambda u: AFun(tau, u, muJ, sigmaJ, xip, k, vb, gamma, l1, sigmarho, d1, v0, krho, murho,\
                            sigmarho, rho4, rho5, T, kr, gammar, mur, c1, c2, r0)

    cf = lambda u: np.exp(aFun(u) + cFun(u)*r0 + dFun(u)*rho0 + eFun(u)*v0)

    return cf
