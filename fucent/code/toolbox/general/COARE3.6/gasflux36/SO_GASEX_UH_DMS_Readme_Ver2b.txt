README for "SO_GASEX_UH_DMS_Flux_Hourly_Ver2b.txt"
Version 2b, 4/4/2011, BWB
Added additional variable with air side DMS concentration in uM/m3 units

This file contains hourly mean data for DMS flux, transfer velocity, and associated variables.
Most associated variables are derived from the Univ. Conn. 10 min meteorological data product
(Sept 2009 version).  Seawater DMS data are from S. Archer, Plymouth Marine Labs, Jan 2010
release.

Variables:

Time_GMT				Time variable, GMT, start of hour for flux measurement
FluxDuration_sec		Duration of flux measurement, seconds
DMS_pptv_air			Atmospheric mean DMS concentration, pptv
DMS_uM_m3_air			Atmospheric mean DMS concentration, uMoles m^-3 at 4 deg C
DMS_uM_m3_sw			Sea water DMS concentration in uMoles m^-3 (or nM)
DMSflux_uM_m2_d			Corrected DMS flux in uMoles m^-2 day^-1 at ambient conditions
DMSflux_error			Flux error (uMoles m^-2 day^-1) computed following Blomquist et al.,2010*
kDMS_cm_hr				DMS transfer velocity for ambient conditions in cm/hr (not Sc corrected)
kDMS_error				Transfer velocity error in cm/hr
U10N_m_s				10 m neutral wind speed in m/s from COARE 3.0 bulk flux model
Ustar_COARE_m_s			Friction velocity in m/s from COARE 3.0
RWspd_m_s				Relative wind speed in m/s
Sc_DMS					DMS Schmidt number at ambient sea surface temperature and salinity
RWdir_deg				Relative wind direction, zero degrees on bow, starboard positive
Tair_C					Air temperature, deg C
SST_C					Sea surface temperature, deg C
Sal_ppth				Salinity in parts per thousand
Lat						GPS latitude
Lon						GPS longitude
SOG_kts					GPS speed over ground in knots
Gyro_deg				Ship gyro heading in degrees
Longwave_w_m2			Longwave radiation
Shortwave_w_m2			Shortwave radiation
z_L						Dimensionless stability parameter, z=18m, L from COARE 3.0.

Notes:

1) DMS flux and transfer velocity measurements have been filtered to remove hours
	of atmospheric stability when z/L > 0.05.
2) Additional periods of anamalously low flux during the first tracer patch and the
	high wind event on transit to Uruguay are not presented in this release.  We
	are currently examining this data to better understand the reason for the low
	results.  For access to these measurements contact the investigators.
	
Contact:  Barry Huebert, University of Hawaii Oceanography, huebert@hawaii.edu
	
*Blomquist et al., Atm.Meas.Tech, 3, 1-20, 2010
