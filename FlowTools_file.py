import numpy as np 
import sys
from scipy import optimize
from CoolProp.CoolProp import PropsSI

R = 8314.34                         # J / (kmol K)


class FlowTools_class():
    '''THIS CLASS IS NECESSARY TO CALCULATE FLUID PROPERTIES: SINGLE PHASE & TWO PHASE \t
    D: diameter [m] \t
    mdotL: subcooled mass rate [kg/s]
    Gt: superficial total mass flux [(kg/s)/m2]
    '''
    def __init__(self, mdotL):
        self.mdotL = mdotL
    
    
    def __str__(self):
        msg = 'This class is used to calculate some two phase mixture\'s properties, such as '
        msg += 'viscoty, specific volume, void fraction ... '
        msg += 'methods with .SEC at the their name end are secundary methods (work in backstage)' 
        return ('What does the class twoPhaseFlowTools_class do? %s'
                '\n--------------------------------------------------------)\n '
                % (msg))

    def volumeEspecificoGas(self, p, T, MMixture):
        '''
        MMixture:  mixture molar weight --> MMixture = np.eisum('i,i', x, MM) [kg/kmol]
        '''
        return ( R * T / (p * MMixture))


    def volumeEspecificaBifasico(self, x, p, T, MMixture, spvolF):
        '''
        x: vapor quality \t
        MMixture:  mixture molar weight 
        spvolF: specific volume saturated liquid [m3/kg]
        '''
        spvolG = self.volumeEspecificoGas(p, T, MMixture)
        return ((1.-x) * spvolF + x * spvolG)

       
    def fracaoVazio(self, x, p, T, MMixture, spvolF):
        '''
        x: vapor quality \t
        MMixture:  mixture molar weight 
        spvolF: specific volume saturated liquid [m3/kg]
        '''
        spvolG = self.volumeEspecificoGas(p, T, MMixture)
        spvolTP = self.volumeEspecificaBifasico(x, p, T, MMixture, spvolF)
        return (spvolG * x / spvolTP)

    def viscO_functionSEC(self, T):

        '''
        This function calculate the POE ISO VG 10 viscosity \n
    
        T: temperature [K] \n
        Oil Viscosity: in [Pa.s] \n


        This correlation has been gotten from: \n 
        Tese de doutorado do Dalton Bertoldi (2014), page 82 \n

        "Investigação Experimental de Escoamentos Bifásicos com mudança \n
        de fase de uma mistura binária em tubo de Venturi" \n
         '''
        Tc = T - 273.15
        return 0.04342 * np.exp(- 0.03529 * Tc)


    def viscR_functionSEC(self, T, p):
        '''
        This function calls CoolProp \n 

        T: temperature [K] \n
        p: pressure [Pa] \n


        Return: Refrigerant's dynamic viscosity [Pa.s]
        '''
        
        return PropsSI("V", "T", T, "P", p,"R134a")

    


    def jpDias_liquidPhaseDensity(self, T, p, xR_mass):
        ''' 
        The correlation was copied from JP Dias's Thesis (pg 294, EQ A.2) \n

        ESCOAMENTO DE ÓLEO E REFRIGERANTE PELA FOLGA PISTÃO-CILINDRO DE 
        COMPRESSORES HERMÉTICOS ALTERNATIVOS (2012) - UFSC \n

        T: temperature [K] \n
        p: pressure [Pa] \n
        xR_mass: vector mass concentration [-] (xR_mass = ([xR_mass, xO_mass])) \n

        This correlation is valid only in interval 20C < temp. celsius < 120C \n

        Return: densL
        '''
        wr = xR_mass[0] * 100.
        Tc = T - 273.15

        densO = 966.43636 - 0.57391608 * Tc - 0.00024475524 * Tc ** 2
        densR = PropsSI("D", "T", T, "P", p,"R134a")
        densL = densO * np.power( (1. + wr * (densO / densR - 1.) ), -1)
        return densL


    def jpDias_liquidViscositySEC(self, T, p, xR_mass):

        ''' 
        The correlation was copied from JP Dias's Thesis (pg 294, EQ A.4) \n

        ESCOAMENTO DE ÓLEO E REFRIGERANTE PELA FOLGA PISTÃO-CILINDRO DE 
        COMPRESSORES HERMÉTICOS ALTERNATIVOS (2012) - UFSC \n

        T: temperature [K] \n
        p: pressure [Pa] \n
        xR_mass: vector mass concentration [-] (xR_mass = ([xR_mass, xO_mass])) \n

        This correlation is valid only in interval: \n
        0 < temp. celsius < 120C and 0.0 < refrigerant < 50.0% \n

        Return: viscL [Pa.s]
        '''

        Tc = T - 273.15
        wr = xR_mass[0] * 100

        (a1, a2) = (38.31853120, 1.0)
        (b1, b2) = (0.03581164, 0.05188487)
        (c1, c2) = (- 0.55465145, 0.02747679)
        (d1, d2) = (- 6.02449153e-5, 9.61400978e-4)
        (e1, e2) = (7.67717272e-4, 4.40945724e-4)
        (f1, f2) = (-2.82836964e-4, 1.10699073e-3)

        num = ( a1 + b1 * Tc + c1 * wr + d1 * np.power(Tc, 2) +
            e1 * np.power(wr, 2) + f1 * Tc * wr) 

        den = ( a2 + b2 * Tc + c2 * wr + d2 * np.power(Tc, 2) +
            e2 * np.power(wr, 2) + f2 * Tc * wr )

        viscCinem = num / den
        densL = self.jpDias_liquidPhaseDensity(T, p, xR_mass)
        return viscCinem * densL * 1e-6
     

    def jpDias_liquidSpecificHeat(self, T, p, xR_mass):
        ''' 
        The correlation was copied from JP Dias's Thesis (pg 295, EQ A.7) \n

        ESCOAMENTO DE ÓLEO E REFRIGERANTE PELA FOLGA PISTÃO-CILINDRO DE 
        COMPRESSORES HERMÉTICOS ALTERNATIVOS (2012) - UFSC \n

        T: temperature [K] \n
        p: pressure [Pa] \n
        xR_mass: vector mass concentration [-] (xR_mass = ([xR_mass, xO_mass])) \n

        This correlation is valid only in interval: ? \n
        

        Return: cpL [J/kg K] (?...tenho verificar se são essas as unidades!!)
        '''
        Tc = T - 273.15
        wr = xR_mass[0] 
        
        CpR = PropsSI("Cpmass", "T", T, "P", p,"R134a")
        CpO = 2411.5968 + 2.260872 * Tc
        return (1. - wr) * CpO + wr * CpR



    def viscosidadeMonofasicoSEC(self, T, p, xR, G12 = 3.5):
        '''
        GRUNBERG & NISSAN (1949) correlation - see Dalton Bertoldi's Thesis (page 81) \n
        Objective: necessary to determine the subcooled liquid's viscosity \n
        T: temperature [K] \n
        p: pressure [Pa] \n
        xR: vector molar concentration ([xR, xO]) \n
        G12: model's parameter (G12 = 3.5 has been taken from Dalton's Thesis (page 82)) \n
        Refrigerant viscosity is get from CoolProp \n
        viscO: Oil's dynamic viscosity [Pa.s] \n
        viscR: Refrigerant's dynamic viscosity [Pa.s]
        '''
        viscO = self.viscO_functionSEC(T)
        viscR = self.viscR_functionSEC(T, p)
        logvisc = np.array([np.log(viscR),np.log(viscO)])
        sum_xlogvisc = np.einsum('i,i', xR, logvisc)
        xRxO_G12 = np.prod(xR) * G12
        return np.exp(sum_xlogvisc + xRxO_G12)



    def reynolds_function(self, Gt, Dc, p, T, xR, xR_mass, visc_model='jpDias'):
        '''
        This function/method calculates Reynolds number \n
        
            The liquid viscosity depend of the model you've been chosen \n
            For while, there are just two options for liquid viscosity \n
        '''
        visc_models = ['jpDias', 'NISSAN']
        if visc_model not in visc_models:
            msg = 'Invalid viscosity model inside function: %s' % sys._getframe().f_code.co_name
            msg += '\t Choose one of the models: %s' % visc_models
            raise Exception(msg)
        if visc_model == 'NISSAN':
            viscL = self.viscosidadeMonofasicoSEC(T, p, xR)
        elif visc_model == 'jpDias':
            viscL = self.jpDias_liquidViscositySEC(T, p, xR_mass)
        return Gt * Dc / viscL 

    

    def frictionChurchillSEC(self, Re, ks, Dc):
        '''
        Churchill equation to estimate Fanning friction factor, f_F, (pg 149, Ron Darby's book) \n
            Can be applied for all flow regimes in single phase \n
            Re: Single phase Reynolds number [-] \n
            ks: rugosity [m] \n
            Dc: diameter [m] \n

        Return: f0 (First estimative for Fanning frictions factor)
        '''
        f1 = 7. / Re
        f2 = 0.27 * ks/Dc
        a = 2.457 * np.log(1. / (f1 ** 0.9 + f2))
        A = a ** 16
        b = 37530. / Re
        B = b ** 16
        f3 = 8. / Re
        return  2 * (f3 ** 12 + 1./(A + B) ** 1.5 ) ** (1. / 12)

    def frictionColebrookSEC(self, Re, ks, Dc):  
        '''This Colebrook function determines the Fanning friction factor \n

            In fluid mechanis Colebrook calculates Darcy factor. Here we convert it to Fanning factor \n
            For Re < 4000 Fanning factor is 16/Re (we added a IF statement for laminar flow case)  \n

        Return: f_F
        '''  
        colebrook = lambda f0: - 2. * np.log10( ks / (3.7 * Dc) + 2.51 / (Re * np.sqrt(f0)) ) - 1. / np.sqrt(f0)
        f0 = 0.25 * (np.log( (ks / Dc) / 3.7 + 5.74 / Re ** 0.9 )) ** (-2) #Fox, pg 234, EQ 8.37b
        f_D = optimize.newton(colebrook, f0)  #Darcy 
        if Re > 2300.: f_F = f_D / 4.
        else: f_F = 16. / Re
        return f_F
    
    
    def frictionFactorFanning(self, Re, ks, Dc, friction_model='Colebrook'):
        '''This is the function/method we must call to calculate Fanning friction factor'''
        friction_models = ['Colebrook', 'Churchill']
        if friction_model not in friction_models:
            msg = 'Invalid friction model inside the function: %s' % sys._getframe().f_code.co_name
            msg += '\t Choose one of the models: %s' % friction_models
            raise Exception(msg)
        if friction_model == 'Churchill':
            f_F = self.frictionChurchillSEC(Re, ks, Dc)
        elif friction_model == 'Colebrook':
            f_F = self.frictionColebrookSEC(Re, ks, Dc)
        return f_F


    def viscosidadeBifasicaSEC(self, x, xR, p, T, MMixture, spvolF):
        '''
        x: vapor quality [-] \t
        xR: vector molar concentration ([xR, xO]) \t
        alfa: void fraction [-] \t
        MMixture:  mixture molar weight --> MMixture = np.eisum('i,i', x, MM) [kg/kmol] \t
        spvolF: specific volume saturated liquid [m3/kg]
         '''
        viscG = 12e-6 #valor qqer...temporário...preciso entrar com uma equação aqui
        viscF = self.viscosidadeMonofasicoSEC(T, p, xR)
        alfa = self.fracaoVazio(x, p, T, MMixture, spvolF)
        return (alfa * viscG + viscF * (1. - alfa) * (1. + 2.5 * alfa))  #Eqc 8.33, pag 213 Ghiaasiaan


    def reynoldsBifasico(self, Gt, Dc, x, xR, p, T, MMixture, spvolF):
        '''
        x: vapor quality [-] \t
        xR: vector molar concentration ([xR, xO])
         '''
        viscTP = self.viscosidadeBifasicaSEC(x, xR, p, T, MMixture, spvolF)
        return (Gt * Dc / viscTP)

    