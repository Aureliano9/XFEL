# -*- coding: utf-8 -*-
"""
Created on Tue Jun 21 16:22:43 2022

@author: lennak
"""

import csv
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import math
import sys
import keyboard
import helpers
import os

from scipy.optimize import curve_fit

# PARAMETERS
# if supplying pump off/on files
pump_off_filename = None
pump_on_filename = None
# if supplying delta A file
delta_A_filenames = ["Data (1)/CudmpDPEphosBF4ACN_1_scan1.csv"] #["sample1/CudmpDPEphosBF4ACN_1_scan2.csv","sample1/CudmpDPEphosBF4ACN_1_scan3.csv","sample1/CudmpDPEphosBF4ACN_1_scan4.csv"]
subtract_surface_files = ["Data (1)/Acetonitrile2.csv"] # "Four approaches for XPM treatment/Acetonitrile2_scan1.csv", 
# time_zero_correction = (-100,-.5) #time units

# READ IN DATA
if pump_off_filename!=None and pump_on_filename!=None:
    wavelengths_off, times_off, pump_off = helpers.read_file(pump_off_filename)
    wavelengths_on, times_on, pump_on = helpers.read_file(pump_on_filename)
    if not np.allclose(wavelengths_off,wavelengths_on) or not np.allclose(times_off,times_on):
        print("Pump off and pump on raw data does not have matching axes")
        sys.exit()
    delta_A = np.log(pump_off/pump_on)
    wavelengths = wavelengths_on
    times = times_on
elif len(delta_A_filenames)!=0:
    if len(delta_A_filenames)==1:
        wavelengths, times, delta_A = helpers.read_file(delta_A_filenames[0])
    else:
        delta_As = []
        for filename in delta_A_filenames:
            wavelengths, times, delta_A = helpers.read_file(filename)
            delta_As.append(delta_A)
        delta_A = np.array(delta_As)

# speed_of_light = 2.99792458e5
# wavelengths = speed_of_light/wavelengths

# RECORD KEEPING
current_wavelength = helpers.avg(wavelengths.min(),wavelengths.max())
current_time = helpers.avg(times.min(),times.max())
wavelength_bounds = (np.min(wavelengths),np.max(wavelengths))
time_bounds = (np.min(times),np.max(times))
c_bounds = (None,None)

# CREATE COPY OF ORIGINAL FOR RESETTING
original_delta_A = np.copy(delta_A)
original_wavelengths = np.copy(wavelengths)
original_times = np.copy(times)


precision = .001
t_eval = np.arange(-.4, .6, precision)
def kovalenko(times, beta, tau1, beta_tau2_sq, D0):
    # beta = 1.7e-3 * 10**6 # chirp rate [ps^-2]
    # tau1 = 50e-3 #ps  ##???
    # # beta_tau1 = 2.2;
    # beta_tau2_sq = 42;
    # D0 = 1
    target_wavelength = 400 ### ADJUST
    center_wavelength = 460 # nm ##???
    speed_of_light = 2.99792458e5 # nm / ps
    omega2 = 2*math.pi*speed_of_light/target_wavelength # rad/ps^-1
    Omega2 = 2*math.pi*speed_of_light/center_wavelength # rad/ps^-1
    t0 = (omega2-Omega2)/(2*beta)# frequency dependent
    return D0*np.exp(-(times+t0)**2/tau1**2)*np.sin(1/(2*beta*tau1**2)-((times+t0)**2/(beta*tau1**4))-((times+t0)*t0/(beta_tau2_sq*tau1**2)))
# target_wavelengths = [400,450,500,550,600,650,700,750] # nm
# for target_wavelength in target_wavelengths:
#     Sk = kovalenko(t_eval, target_wavelength)
#     plt.figure()
#     plt.plot(t_eval,Sk)
#     plt.title("Kovalenko: Wavelength = "+ str(target_wavelength))
#     plt.show()

def ours(times, c1, c2, c3):
    beta = 1.7e-3 * 10**6 # chirp rate [ps^-2]
    tau1 = 50e-3 #ps  ##???
    target_wavelength = 400 #### ADJUST
    center_wavelength = 460 # nm ##???
    speed_of_light = 2.99792458e5 # nm / ps
    omega2 = 2*math.pi*speed_of_light/target_wavelength # rad/ps^-1
    Omega2 = 2*math.pi*speed_of_light/center_wavelength # rad/ps^-1
    t0 = (omega2-Omega2)/(2*beta)# frequency dependent
    # c1 = t0/(2*beta)
    # c2 = t0/(2*beta)
    # c3 = -1/(4*beta)
    return np.exp(-(times+t0)**2/tau1**2)*(c1-c2*2*(times+t0)/tau1**2-c3*(2/tau1**2-4*(times+t0)**2/tau1**4))

# for target_wavelength in target_wavelengths:
#     So = ours(t_eval, target_wavelength)
#     plt.figure()
#     plt.plot(t_eval,So)
#     plt.title("Ours: Wavelength = "+ str(target_wavelength))
#     plt.show()

# popt, pcov = curve_fit(kovalenko, times, delta_A[:,helpers.find_index(wavelengths,400)], [163, 50e-3, 42, .001])
# print(popt)
# fitted = kovalenko(times, popt[0], popt[1], popt[2], popt[3])
# plt.figure()
# plt.plot(times, delta_A[:,helpers.find_index(wavelengths,400)])
# plt.plot(times, fitted)
# plt.show()

# def lorenc(times):
#     alpha = 1
#     omega = 1
#     beta = 1.7e-3 * 10**6
#     tau = 50e-3
#     tau_gvd = 150e-3 #fs
#     return 2*np.log(1+alpha*omega/(beta*tau**2*tau_gvd)*(times*np.exp(-2*times**2/tau**2)-(times-tau_gvd)*np.exp(-2*(times-tau_gvd)**2/tau**2)))
# Sl = lorenc(t_eval)
# plt.figure()
# plt.plot(t_eval,Sl)
# plt.title("Lorenc")
# plt.show()

# MENU
menu = {}
menu["q"] = "quit"
menu["wc"] = "change current wavelength"
menu["tc"] = "change current time"
menu["tp"] = "plot cross-section at current wavelength s.t. time is x-axis"
menu["wp"] = "plot cross-section at current time s.t. wavelength is x-axis"
menu["cp"] = "plot 2D color signal"
menu["waxis"] = "change wavelength axis bounds"
menu["taxis"] = "change time axis bounds"
menu["caxis"] = "change color axis bounds"
menu["reset axis"] = "reset wavelength/time/color axis bounds"
menu["p"] = "play wavelength cross-sections over all time"
menu["subtract"] = "subtract surfact from current working surface"
menu["avg"] = "take average of signal across multiple files"
menu["shift time"] = "shift time values"
menu["cut w"] = "cut out wavelength range"
menu["spikes"] = "remove spikes"
menu["nan w"] = "remove nan wavelength spectra"
menu["nan t"] = "remove nan time spectra"
menu["background"] = "perform background correction"
menu["chirp"] = "perform chirp correction"
menu["reset data"] = "reset all data changes"

# LIVE INTERACTION
while True:
    action = input("Action? (enter 'm' to see command menu)\n")
    if action=="q":
        print("quitting...")
        break
    elif action=="m":
        print("displaying menu...\n")
        width  = 20
        print(f"{'Type' : <20}{'Command' : <20}")
        for key in menu:
            value = menu[key]
            print(f"{key : <20}{value : <20}")
    elif action=="wc":
        print("changing wavelength value...")
        new_w = helpers.ask_value(float, "wavelength")
        if new_w!=None:
            current_wavelength = new_w
    elif action=="tc":
        print("changing time value...")
        new_t = helpers.ask_value(float, "time")
        if new_t!=None:
            current_time = new_t
    elif action=="wp":
        print("plotting wavelength plot...")
        if delta_A.ndim==2:
            helpers.plot_crosssection(wavelengths,times,delta_A,current_time,True,wavelength_bounds)
        elif delta_A.ndim==3:
            print("still have not taken average")
            display_index = helpers.ask_value(int, override_text="What layer would you like to display? ")
            helpers.plot_crosssection(wavelengths,times,delta_A[display_index,:,:],current_time,True,wavelength_bounds)
    elif action=="tp":
        print("plotting time plot...")
        if delta_A.ndim==2:
            helpers.plot_crosssection(wavelengths,times,delta_A,current_wavelength,False,time_bounds)
        elif delta_A.ndim==3:
            print("still have not taken average")
            display_index = helpers.ask_value(int, override_text="What layer would you like to display? ")
            helpers.plot_crosssection(wavelengths,times,delta_A[display_index,:,:],current_wavelength,False,time_bounds)
    elif action=="cp":
        print("plotting color plot...")
        if delta_A.ndim==2:
            helpers.plot_color(wavelengths, times, delta_A, current_wavelength, current_time, w_bounds=wavelength_bounds, t_bounds=time_bounds, c_bounds=c_bounds)
        elif delta_A.ndim==3:
            print("still have not taken average")
            display_index = helpers.ask_value(int, override_text="What layer would you like to display? ")
            if display_index!=None and display_index<delta_A.shape[0]:
                helpers.plot_color(wavelengths, times, delta_A[display_index,:,:], current_wavelength, current_time, w_bounds=wavelength_bounds, t_bounds=time_bounds, c_bounds=c_bounds)
            else:
                print("Invalid index. Index ranges from 0 to " + str(delta_A.shape[0]-1))
    elif action=="waxis":
        print("changing wavelength axis...")
        wavelength_bounds = helpers.ask_range(float, default = wavelength_bounds)
    elif action=="taxis":
        print("changing time axis...")
        time_bounds = helpers.ask_range(float, default = time_bounds)
    elif action=="caxis":
        print("changing color axis...")
        c_bounds = helpers.ask_range(float, default = c_bounds)
    elif action=="reset axis":
        print("reseting axis...")
        which_axis = helpers.ask_value(int, default=None, override_text="Which axis to reset? (0=wavelength, 1=time, 2=color, 3=all) ")
        if which_axis==0:
            wavelength_bounds = (np.min(wavelengths),np.max(wavelengths))
        elif which_axis==1:
            time_bounds = (np.min(times),np.max(times))
        elif which_axis==2:
            c_bounds = (None,None)
        elif which_axis==3:
            wavelength_bounds = (np.min(wavelengths),np.max(wavelengths))
            time_bounds = (np.min(times),np.max(times))
            c_bounds = (None,None)
        else:
            print("Must specify axis with 0, 1, 2, 3")
    elif action=="play":
        print("playing with time...")
        for i in range(len(times)):
            helpers.plot_crosssection(wavelengths,times,delta_A,i,True,wavelength_bounds)
        repeat_flag = input("Repeat? (y/n)")
        if repeat_flag!="y":
            break
    elif action=="t peak":
        print("Find peak in given range")
        time_min_index = helpers.find_index(times,time_bounds[0])
        time_max_index = helpers.find_index(times,time_bounds[1])
        wavelength_index = helpers.find_index(wavelengths,current_wavelength)
        peak_index = time_min_index + np.argmax(delta_A[time_min_index:time_max_index,wavelength_index])
        print("Peak at time: ", times[peak_index])
    # MUTATING DATA
    elif action=="subtract":
        # SUBTRACT SURFACE IF NEEDED
        print("subtracting surface...")
        print("Candidate surfaces to subtract with:", subtract_surface_files)
        index = helpers.ask_value(int, default=None, override_text="Specify with index (-1 for custom filename): ")
        if index==-1:
            subtract_surface_file = input("Filename? ")
        elif index!=None:
            subtract_surface_file = subtract_surface_files[index]
        else:
            print("no file specified")
            subtract_surface_file = ""
        
        if subtract_surface_file!="":
            wavelengths_subtract, times_subtract, subtract_surface = helpers.read_file(subtract_surface_file)
            print("Original shape:", delta_A.shape)
            print("Subtract shape:", subtract_surface.shape)
            Er = helpers.ask_value(float, default=None, override_text="Energy for subtract surface: ") #650
            Es = helpers.ask_value(float, default=None, override_text="Energy for original surface: ") #500
            f = helpers.ask_value(float, default=None, override_text="Fraction f: ")
            
            print(min(wavelengths_subtract),max(wavelengths_subtract))
            print(min(times_subtract),max(times_subtract))
            
            if Es!=None and Er!=None and f!=None:
                # subtract surface 
                for i in range(len(times_subtract)):
                    delta_A_index = helpers.find_index(times, times_subtract[i])
                    if delta_A.ndim==3:
                        for i in range(3):
                            delta_A[i,delta_A_index,:] -= (Es*f/Er) * subtract_surface[i,:]
                    else:
                        delta_A[delta_A_index,:] -= (Es*f/Er) * subtract_surface[i,:]
            else:
                print("Error: Enter valid value")
                    
    elif action=="avg":
        if delta_A.ndim==3:
            delta_A = np.nanmean(delta_A, axis=0)
        else:
            print("only one file")
    elif action=="shift time":
        uniform_time_shift = helpers.ask_value(float, default=0)
        times += uniform_time_shift
        time_bounds = (time_bounds[0]+uniform_time_shift,time_bounds[1]+uniform_time_shift)
    elif action=="cut w":
        print("cutting wavelength range...") # ask user nan/delete
        cut_min, cut_max = helpers.ask_range(float)
        cut_min_index = helpers.find_index(wavelengths, cut_min)
        cut_max_index = helpers.find_index(wavelengths, cut_max)
        nan_flag = input("replace with nan? otherwise, will delete. (y/n)")
        if nan_flag=="y":
            if delta_A.ndim == 2:
                delta_A[:,cut_min_index:cut_max_index] = np.NaN
            elif delta_A.ndim == 3:
                delta_A[:,:,cut_min_index:cut_max_index] = np.NaN
            else:
                print("ERROR: data has dimension", delta_A.ndim)
                os.abort()
        else:
            if delta_A.ndim == 2:
                delta_A = np.concatenate((delta_A[:,:cut_min_index],delta_A[:,cut_max_index:]), axis=1)
            elif delta_A.ndim == 3:
                delta_A = np.concatenate((delta_A[:,:,:cut_min_index],delta_A[:,:,cut_max_index:]), axis=2)
            else:
                print("ERROR: data has dimension", delta_A.ndim)
                os.abort()
        wavelengths = np.concatenate((wavelengths[:cut_min_index],wavelengths[cut_max_index:]))
    elif action=="spikes":
        print("removing spikes...")
        width = helpers.ask_value(int,"width for spikes")
        factor = helpers.ask_value(float,"number of standard deviations allowed")
        if width!=None and factor!=None:
            delta_A = helpers.remove_spikes(delta_A, width, factor)
    elif action=="nan w":
        print("removing nan wavelength spectra...")
        if delta_A.ndim==3:
            print("Take avg first before removing spectra")
        else:
            print("Old dimension: " + str(delta_A.shape))
            remove = []
            for t in range(len(times)):
                if np.any(np.isnan(delta_A[t,:])):
                    remove.append(t)
            remove.reverse()
            for t in remove:
                if t==len(times)-1:
                    delta_A = delta_A[:t,:]
                    times = times[:t]
                else:
                    delta_A = np.concatenate((delta_A[:t,:],delta_A[t+1:,:]),axis=0)
                    times = np.concatenate((times[:t],times[t+1:]))
            remove.clear()
            print("New dimension: " + str(delta_A.shape))
    elif action=="nan t":
        print("removing nan time spectra...")
        if delta_A.ndim==3:
            print("Take avg first before removing spectra")
        else:
            remove = []
            for w in range(len(wavelengths)):
                if (delta_A.ndim==2 and np.any(np.isnan(delta_A[:,w]))) or (delta_A.ndim==3 and np.any(np.isnan(delta_A[:,:,w]))):
                    remove.append(w)
            remove.reverse()
            for w in remove:
                if w==len(times)-1:
                    delta_A = delta_A[:,:,:w]
                    wavelengths = wavelengths[:w]
                else:
                    delta_A = np.concatenate((delta_A[:,:w],delta_A[:,w+1:]),axis=0)
                    wavelengths = np.concatenate((wavelengths[:w],wavelengths[w+1:]))
            print("New dimension is " + str(delta_A.shape))
    elif action=="background":
        print("performing background correction...")
        cont_flag = input("Warning: average was not taken yet. Continue? (y/n) ")
        if cont_flag=="y":
            back_min, back_max = helpers.ask_range(float)
            if back_min!=None and back_max!=None:
                background_index = (helpers.find_index(times,back_min),helpers.find_index(times,back_max))
                if delta_A.ndim==2:
                    delta_A -= np.nanmean(delta_A[background_index[0]:background_index[1],:],axis=0)
                elif delta_A.ndim==3:
                    background = np.nanmean(delta_A[:,background_index[0]:background_index[1],:],axis=1)
                    for i in range(delta_A.shape[0]):
                        delta_A[i,:,:] -= background[i,:]
    elif action=="chirp":
        print("performing chirp correction...")
        delta_A = helpers.chirp_correction(times,wavelengths,delta_A)
    elif action=="reset data":
        print("reseting to original data...")
        delta_A = original_delta_A
        wavelengths = original_wavelengths
        times = original_times
        wavelength_bounds = (np.min(wavelengths),np.max(wavelengths))
        time_bounds = (np.min(times),np.max(times))
        c_bounds = (None,None)
    else:
        print("error, did not recognize command")
    