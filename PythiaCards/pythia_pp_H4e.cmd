! 1) Settings used in the main program.
Main:numberOfEvents = 1000         ! number of events to generate
Main:timesAllowErrors = 100        ! how many aborts before run stops
Random:setSeed = on
Random:seed = 0

! 2) Settings related to output in init(), next() and stat().
Init:showChangedSettings = on      ! list changed settings
Init:showChangedParticleData = off ! list changed particle data
Next:numberCount = 100             ! print message every n events
Next:numberShowInfo = 1            ! print event information n times
Next:numberShowProcess = 1         ! print process record n times
Next:numberShowEvent = 0           ! print event record n times

ParticleDecays:tau0Max = 10        ! ... if c*tau0 > 10 mm
ParticleDecays:limitCylinder = on
ParticleDecays:xyMax = 20          ! mm
ParticleDecays:zMax = 30000        ! mm, (full extent of beampipe)

####################
######SPECIFIC######
####################
HiggsSM:gg2H = on
25:onMode = off
25:onIfAny = 23
23:onMode = off
23:onIfAny = 11
PartonLevel:MPI = on            

