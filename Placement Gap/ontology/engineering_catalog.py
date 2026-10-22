from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

DATA = Path(__file__).parent / "data"


BRANCHES: dict[str, dict[str, Any]] = {
    "Computer Science & IT": {
        "overview": "Software, data, infrastructure, security, and digital product careers.",
        "foundation": "Programming, algorithms, databases, operating systems, networks, and software delivery.",
        "toolchain": "Git, a primary programming language, command-line tools, testing, and versioned project work.",
        "practice": "Build secure, accessible, testable systems; document trade-offs and validate work with users.",
        "provider": "Microsoft Learn",
        "course_url": "https://learn.microsoft.com/en-us/training/",
    },
    "Electronics & Communication": {
        "overview": "Electronics, embedded systems, semiconductors, communications, and signal processing careers.",
        "foundation": "Circuit analysis, analog and digital electronics, signals and systems, semiconductor devices, and programming.",
        "toolchain": "Python or C, MATLAB/Simulink, circuit simulation, oscilloscopes, datasheets, and a microcontroller or FPGA workflow.",
        "practice": "Validate simulations with measurements; account for noise, tolerances, electrical safety, and clear design records.",
        "provider": "NPTEL",
        "course_url": "https://nptel.ac.in/courses",
        "secondary_provider": "MathWorks MATLAB Academy",
        "secondary_course": "MATLAB Onramp and Simulink Onramp",
        "secondary_url": "https://matlabacademy.mathworks.com/",
    },
    "Electrical Engineering": {
        "overview": "Power, control, automation, energy, electric mobility, and electrical systems careers.",
        "foundation": "Circuit theory, electrical machines, power systems, control, power electronics, and engineering mathematics.",
        "toolchain": "MATLAB/Simulink, Python, electrical CAD or simulation, PLC/SCADA concepts, and measurement instruments.",
        "practice": "Use safe isolation procedures, protection coordination, standards-aware design, and documented calculations.",
        "provider": "NPTEL",
        "course_url": "https://nptel.ac.in/courses",
        "secondary_provider": "MathWorks MATLAB Academy",
        "secondary_course": "MATLAB Onramp and Simulink Onramp",
        "secondary_url": "https://matlabacademy.mathworks.com/",
    },
    "Mechanical Engineering": {
        "overview": "Product design, manufacturing, thermal systems, mobility, robotics, and mechanical reliability careers.",
        "foundation": "Engineering mechanics, materials, thermodynamics, fluid mechanics, manufacturing, and mechanical design.",
        "toolchain": "Parametric CAD, drawings and GD&T, MATLAB or Python, simulation, measurement, and manufacturing documentation.",
        "practice": "Check units, loads, tolerances, material selection, machine safety, and design-for-manufacture constraints.",
        "provider": "NPTEL",
        "course_url": "https://nptel.ac.in/courses",
        "secondary_provider": "Autodesk Learning",
        "secondary_course": "Fusion learning pathways for 3D design and manufacturing",
        "secondary_url": "https://www.autodesk.com/learning.autodesk",
        "tertiary_provider": "ANSYS Innovation Courses",
        "tertiary_course": "Free engineering simulation courses",
        "tertiary_url": "https://innovationspace.ansys.com/courses/",
    },
    "Civil Engineering": {
        "overview": "Structures, infrastructure, geotechnics, transport, water, construction, and the built environment careers.",
        "foundation": "Engineering mechanics, surveying, materials, structural analysis, geotechnics, and construction methods.",
        "toolchain": "CAD/BIM, spreadsheets, surveying or GIS tools, structural analysis software, and quantity/document controls.",
        "practice": "Prioritize public safety, design-code awareness, site quality records, environmental impacts, and checked calculations.",
        "provider": "NPTEL",
        "course_url": "https://nptel.ac.in/courses",
        "secondary_provider": "Autodesk Learning",
        "secondary_course": "Civil 3D, Revit, and BIM learning pathways",
        "secondary_url": "https://www.autodesk.com/learning.autodesk",
    },
    "Chemical Engineering": {
        "overview": "Process design, production, safety, energy, materials, biotechnology, and industrial chemistry careers.",
        "foundation": "Material and energy balances, thermodynamics, fluid flow, heat and mass transfer, reaction engineering, and process control.",
        "toolchain": "Spreadsheets, Python or MATLAB, process-flow diagrams, simulation concepts, and laboratory data analysis.",
        "practice": "Use process-safety thinking, hazard reviews, mass-balance checks, environmental controls, and traceable operating data.",
        "provider": "NPTEL",
        "course_url": "https://nptel.ac.in/courses",
        "secondary_provider": "LearnChemE · University of Colorado Boulder",
        "secondary_course": "Interactive chemical engineering modules and simulations",
        "secondary_url": "https://learncheme.com/",
    },
}


# (title, specialty focus, portfolio project, required skills, preferred skills)
ROLE_ROWS: dict[str, list[tuple[str, str, str, tuple[str, ...], tuple[str, ...]]]] = {
    "Electronics & Communication": [
        ("Embedded Systems Engineer", "firmware that connects sensors, microcontrollers, and reliable real-time behavior", "Build a sensor node with a documented interface, test plan, and measured power budget", ("C Programming", "Embedded Systems", "Microcontrollers", "Digital Electronics", "Circuit Analysis", "Debugging"), ("RTOS", "PCB Design")),
        ("VLSI Design Engineer", "digital logic, synthesis, timing, and implementation of integrated circuits", "Design a small RTL block, verify it with a testbench, and document timing assumptions", ("Digital Logic Design", "Verilog", "VLSI Design", "Digital Electronics", "Semiconductor Devices", "Computer Architecture"), ("SystemVerilog", "Static Timing Analysis")),
        ("VLSI Verification Engineer", "verification plans, assertions, coverage, and reproducible digital-design testing", "Create a verification plan and testbench for a parameterized RTL component", ("Verilog", "SystemVerilog", "Digital Logic Design", "VLSI Verification", "Digital Electronics", "Debugging"), ("Functional Coverage", "UVM")),
        ("RF Engineer", "radio-frequency circuits, impedance matching, propagation, and measurement", "Model and characterize a simple RF link with assumptions and measurement notes", ("RF Engineering", "Electromagnetics", "Circuit Analysis", "Signals and Systems", "MATLAB", "Measurement and Instrumentation"), ("Microwave Engineering", "Antenna Design")),
        ("Telecommunications Engineer", "communication networks, link budgets, protocols, and service reliability", "Plan a small wireless link and explain capacity, coverage, and failure trade-offs", ("Communication Systems", "Computer Networks", "Signals and Systems", "Digital Signal Processing", "Probability and Statistics", "Python"), ("5G Networks", "Network Optimization")),
        ("Signal Processing Engineer", "discrete-time signals, filtering, spectral analysis, and algorithm validation", "Implement and evaluate a signal-processing pipeline on a reproducible dataset", ("Digital Signal Processing", "Signals and Systems", "MATLAB", "Python", "Probability and Statistics", "Algorithm Design"), ("Machine Learning", "Audio Signal Processing")),
        ("PCB Design Engineer", "schematic capture, component selection, layout, fabrication constraints, and board testing", "Create a reviewed two-layer PCB package with a bill of materials and bring-up checklist", ("PCB Design", "Circuit Design", "Analog Electronics", "Digital Electronics", "Electronic Design Automation", "Design for Manufacturing"), ("Signal Integrity", "EMI/EMC")),
        ("Firmware Engineer", "low-level drivers, device interfaces, memory constraints, and embedded debugging", "Write a tested driver for a sensor and provide a reproducible hardware-in-loop demo", ("C Programming", "Firmware Development", "Embedded Systems", "Microcontrollers", "Digital Electronics", "Git"), ("RTOS", "Embedded Linux")),
        ("Hardware Test Engineer", "test fixtures, automated measurements, failure isolation, and release evidence", "Build a repeatable test plan and Python-based measurement report for a circuit board", ("Hardware Testing", "Measurement and Instrumentation", "Python", "Circuit Analysis", "Electronics Testing", "Technical Documentation"), ("LabVIEW", "Reliability Engineering")),
        ("Semiconductor Process Engineer", "device fabrication steps, process windows, metrology, and yield improvement", "Analyze a sample process dataset and propose a measurable yield experiment", ("Semiconductor Manufacturing", "Semiconductor Devices", "Process Engineering", "Statistical Process Control", "Materials Science", "Data Analysis"), ("Cleanroom Safety", "Yield Engineering")),
        ("FPGA Engineer", "RTL implementation, synthesis, timing closure, and hardware validation", "Implement a streaming data module on an FPGA development board with timing notes", ("FPGA Design", "Verilog", "Digital Logic Design", "Computer Architecture", "Embedded Systems", "Hardware Testing"), ("SystemVerilog", "High-Level Synthesis")),
        ("Antenna Design Engineer", "antenna fundamentals, electromagnetic simulation, matching, and measurement", "Design and document a simple antenna study with a simulated and measured comparison", ("Antenna Design", "Electromagnetics", "RF Engineering", "MATLAB", "Measurement and Instrumentation", "Signals and Systems"), ("Microwave Engineering", "Antenna Measurement")),
        ("IoT Systems Engineer", "connected sensing devices, embedded firmware, communication, and secure telemetry", "Prototype an end-to-end sensor system with a device, data path, and threat notes", ("Internet of Things", "Embedded Systems", "Microcontrollers", "Computer Networks", "Python", "Cybersecurity"), ("MQTT", "Cloud Computing")),
        ("Electronics Design Engineer", "analog and digital circuit design, component trade-offs, and prototype validation", "Design and validate a mixed-signal subsystem with calculations and test results", ("Circuit Design", "Analog Electronics", "Digital Electronics", "Circuit Analysis", "PCB Design", "Measurement and Instrumentation"), ("SPICE Simulation", "Power Electronics")),
        ("Instrumentation Engineer", "sensors, signal conditioning, calibration, and measurement-system integration", "Build a calibrated measurement chain and report uncertainty and repeatability", ("Instrumentation Engineering", "Sensors", "Measurement and Instrumentation", "Analog Electronics", "Control Systems", "Data Analysis"), ("LabVIEW", "Industrial Automation")),
        ("Optical Communications Engineer", "fiber links, optical components, link budgets, and system performance", "Model an optical link budget and document loss, bandwidth, and test assumptions", ("Optical Communications", "Communication Systems", "Electromagnetics", "Signals and Systems", "MATLAB", "Measurement and Instrumentation"), ("Fiber Optics", "Photonic Devices")),
        ("Automotive Electronics Engineer", "vehicle electronics, embedded control, communication buses, and validation", "Prototype a vehicle subsystem controller with a fault-response test plan", ("Automotive Electronics", "Embedded Systems", "Microcontrollers", "Control Systems", "CAN Bus", "Hardware Testing"), ("Functional Safety", "Electric Vehicles")),
        ("Electronics Applications Engineer", "customer requirements, product selection, prototypes, and technical problem solving", "Turn a customer use case into a tested reference design and clear application note", ("Electronics", "Circuit Analysis", "Communication", "Technical Writing", "Problem Solving", "Product Demonstration"), ("PCB Design", "Semiconductor Devices")),
    ],
    "Electrical Engineering": [
        ("Power Systems Engineer", "generation, transmission, load flow, and grid reliability", "Analyze a small power network and explain operating limits and contingencies", ("Power Systems", "Circuit Analysis", "Electrical Machines", "MATLAB", "Power System Analysis", "Engineering Mathematics"), ("Renewable Energy", "Power System Protection")),
        ("Power Protection Engineer", "relay coordination, fault analysis, protection schemes, and safe system operation", "Produce a protection-coordination study for a sample feeder with assumptions", ("Power System Protection", "Power Systems", "Electrical Machines", "Circuit Analysis", "Power System Analysis", "Technical Documentation"), ("IEC Standards", "Substation Automation")),
        ("Renewable Energy Engineer", "solar and wind systems, resource assessment, grid connection, and performance", "Size a small renewable system and report energy yield and grid assumptions", ("Renewable Energy", "Power Systems", "Power Electronics", "MATLAB", "Energy Systems", "Data Analysis"), ("Solar Photovoltaics", "Wind Energy")),
        ("Power Electronics Engineer", "converters, switching devices, control loops, and thermal trade-offs", "Simulate and test a DC-DC converter with efficiency and ripple measurements", ("Power Electronics", "Circuit Analysis", "Control Systems", "MATLAB", "Electrical Machines", "Thermal Engineering"), ("PCB Design", "Electric Vehicles")),
        ("Electrical Design Engineer", "load estimation, equipment selection, schematics, and installation packages", "Prepare an electrical design package with load schedules and review checks", ("Electrical Design", "Circuit Analysis", "Electrical CAD", "Power Systems", "Technical Documentation", "Project Management"), ("Building Services", "IEC Standards")),
        ("Substation Engineer", "primary equipment, single-line diagrams, grounding, and commissioning coordination", "Create a substation equipment and inspection package for a sample project", ("Substation Engineering", "Power Systems", "Electrical Design", "Power System Protection", "Electrical Safety", "Technical Documentation"), ("SCADA", "High Voltage Engineering")),
        ("Electrical Machines Engineer", "machine behavior, testing, losses, drives, and application selection", "Compare machine performance from a modeled and measured operating point", ("Electrical Machines", "Circuit Analysis", "Power Electronics", "MATLAB", "Measurement and Instrumentation", "Control Systems"), ("Electric Drives", "Finite Element Analysis")),
        ("Control Systems Engineer", "dynamic modeling, feedback design, stability, and system commissioning", "Model and tune a closed-loop system, then document stability and test results", ("Control Systems", "MATLAB", "Signals and Systems", "Engineering Mathematics", "Python", "System Modeling"), ("Simulink", "Robotics")),
        ("PLC Automation Engineer", "PLC logic, sensors, actuators, industrial networks, and safe machine sequencing", "Simulate a small automated cell with interlocks and a fault recovery sequence", ("PLC Programming", "Industrial Automation", "Control Systems", "Sensors", "Electrical Safety", "Technical Documentation"), ("SCADA", "Industrial Networking")),
        ("Electric Vehicle Systems Engineer", "traction systems, batteries, power conversion, charging, and vehicle integration", "Create a small EV subsystem model with an energy and thermal budget", ("Electric Vehicles", "Power Electronics", "Electrical Machines", "Battery Systems", "Control Systems", "MATLAB"), ("Automotive Electronics", "Functional Safety")),
        ("Energy Efficiency Engineer", "energy audits, consumption baselines, system losses, and savings verification", "Prepare an energy-audit report with a quantified improvement plan", ("Energy Auditing", "Energy Systems", "Data Analysis", "Electrical Machines", "Building Services", "Technical Writing"), ("Renewable Energy", "Energy Management")),
        ("Smart Grid Engineer", "grid sensing, automation, distributed energy, and data-aware operations", "Design a smart-feeder concept with telemetry, control boundaries, and resilience checks", ("Smart Grids", "Power Systems", "Computer Networks", "SCADA", "Python", "Cybersecurity"), ("Renewable Energy", "Power System Protection")),
        ("High Voltage Engineer", "insulation coordination, electrical testing, clearances, and high-voltage safety", "Document a high-voltage test plan and insulation-coordination study", ("High Voltage Engineering", "Power Systems", "Electrical Safety", "Measurement and Instrumentation", "Electrical Design", "Technical Documentation"), ("Power System Protection", "IEC Standards")),
        ("Electrical Commissioning Engineer", "installation checks, functional tests, energization readiness, and handover", "Build a commissioning checklist and test record for a sample installation", ("Electrical Commissioning", "Electrical Safety", "Electrical Design", "Power Systems", "Troubleshooting", "Technical Documentation"), ("Substation Engineering", "SCADA")),
        ("Electric Drives Engineer", "motor-drive sizing, speed control, converter selection, and performance testing", "Model a motor drive and document speed-torque behavior and protection", ("Electric Drives", "Electrical Machines", "Power Electronics", "Control Systems", "MATLAB", "Measurement and Instrumentation"), ("Electric Vehicles", "Industrial Automation")),
        ("Electrical Maintenance Engineer", "preventive maintenance, diagnostics, failure analysis, and equipment availability", "Create a risk-based maintenance plan with inspection and fault-trend records", ("Electrical Maintenance", "Electrical Machines", "Troubleshooting", "Electrical Safety", "Reliability Engineering", "Data Analysis"), ("Power System Protection", "Condition Monitoring")),
        ("Building Services Engineer", "building electrical systems, lighting, backup power, coordination, and code-aware design", "Prepare a coordinated electrical services package for a sample building floor", ("Building Services", "Electrical Design", "Electrical CAD", "Power Systems", "Energy Efficiency", "Technical Documentation"), ("BIM", "Renewable Energy")),
        ("Electrical R&D Engineer", "prototyping, modeling, experiments, and evidence-based improvements to electrical systems", "Publish a reproducible experiment with a model, measured data, and design decision", ("Electrical Engineering", "Circuit Analysis", "MATLAB", "Measurement and Instrumentation", "Data Analysis", "Technical Writing"), ("Power Electronics", "Research Methods")),
    ],
    "Mechanical Engineering": [
        ("Mechanical Design Engineer", "mechanism and component design, calculations, drawings, and design reviews", "Design a load-bearing assembly with drawings, calculations, and a test plan", ("Mechanical Design", "CAD", "Engineering Mechanics", "Materials Science", "GD&T", "Design for Manufacturing"), ("Finite Element Analysis", "SolidWorks")),
        ("CAD Design Engineer", "parametric parts, assemblies, drawings, and controlled design revisions", "Create a parametric assembly and drawing package with a revision history", ("CAD", "Mechanical Design", "GD&T", "Technical Drawing", "Design for Manufacturing", "Technical Documentation"), ("Autodesk Fusion", "SolidWorks")),
        ("Manufacturing Engineer", "process selection, work instructions, cycle time, and production readiness", "Map a manufacturing process and propose a measurable quality or throughput improvement", ("Manufacturing Processes", "Lean Manufacturing", "Quality Engineering", "CAD", "Statistical Process Control", "Project Management"), ("CNC Machining", "Automation")),
        ("Production Engineer", "daily production systems, line balancing, process capability, and defect reduction", "Analyze a production-line dataset and present a validated improvement experiment", ("Production Engineering", "Lean Manufacturing", "Statistical Process Control", "Quality Engineering", "Data Analysis", "Problem Solving"), ("Six Sigma", "Manufacturing Automation")),
        ("Thermal Systems Engineer", "heat transfer, thermodynamic cycles, thermal sizing, and performance validation", "Model a thermal system and compare predicted output with a measured or reference case", ("Thermodynamics", "Heat Transfer", "Fluid Mechanics", "MATLAB", "Thermal Engineering", "Engineering Mathematics"), ("CFD", "HVAC")),
        ("HVAC Design Engineer", "heating and cooling loads, duct and piping systems, equipment selection, and commissioning", "Prepare a small building HVAC concept with load assumptions and equipment schedule", ("HVAC", "Thermodynamics", "Heat Transfer", "Fluid Mechanics", "CAD", "Building Services"), ("Revit", "Energy Efficiency")),
        ("Automotive Design Engineer", "vehicle components, packaging, materials, manufacturing, and durability constraints", "Develop a vehicle component concept with a CAD package and basic validation plan", ("Automotive Engineering", "Mechanical Design", "CAD", "Materials Science", "Finite Element Analysis", "Manufacturing Processes"), ("Vehicle Dynamics", "Electric Vehicles")),
        ("Aerospace Structures Engineer", "lightweight structures, load paths, material trade-offs, and verification", "Analyze a representative structural part and document load cases and margins", ("Aerospace Engineering", "Structural Analysis", "Finite Element Analysis", "Materials Science", "CAD", "Technical Documentation"), ("Composite Materials", "Fatigue Analysis")),
        ("Robotics Engineer", "robot mechanisms, actuation, sensing, motion, and safe integration", "Build or simulate a robot task with a kinematic model and repeatable tests", ("Robotics", "Control Systems", "CAD", "Python", "Sensors", "Embedded Systems"), ("ROS", "Computer Vision")),
        ("Mechatronics Engineer", "mechanical assemblies integrated with electronics, firmware, and control", "Prototype an electromechanical system with interface and safety documentation", ("Mechatronics", "Mechanical Design", "Embedded Systems", "Control Systems", "Sensors", "CAD"), ("PLC Programming", "Robotics")),
        ("Finite Element Analysis Engineer", "mesh quality, boundary conditions, material models, and result interpretation", "Validate an FEA model against hand calculations or a benchmark case", ("Finite Element Analysis", "Structural Analysis", "Materials Science", "Mechanical Design", "Engineering Mathematics", "ANSYS"), ("Fatigue Analysis", "Python")),
        ("CFD Engineer", "fluid domains, mesh independence, turbulence assumptions, and result validation", "Run a documented CFD study with a mesh check and physical sanity review", ("Computational Fluid Dynamics", "Fluid Mechanics", "Thermodynamics", "Numerical Methods", "ANSYS", "Python"), ("Heat Transfer", "MATLAB")),
        ("Mechanical Quality Engineer", "inspection plans, root-cause analysis, tolerance control, and supplier quality", "Create an inspection plan and use sample data to investigate a defect trend", ("Quality Engineering", "GD&T", "Manufacturing Processes", "Statistical Process Control", "Root Cause Analysis", "Technical Documentation"), ("Six Sigma", "Reliability Engineering")),
        ("Maintenance and Reliability Engineer", "asset strategy, failure modes, maintenance planning, and condition monitoring", "Complete a failure-mode review and propose a measurable maintenance strategy", ("Reliability Engineering", "Mechanical Maintenance", "Root Cause Analysis", "Data Analysis", "Mechanical Systems", "Safety Engineering"), ("Condition Monitoring", "Predictive Maintenance")),
        ("Materials Engineer", "material selection, processing, failure analysis, and property validation", "Compare candidate materials for a component and justify the selection with evidence", ("Materials Science", "Materials Testing", "Manufacturing Processes", "Failure Analysis", "Mechanical Design", "Data Analysis"), ("Metallurgy", "Composite Materials")),
        ("Tooling Engineer", "fixtures, jigs, dies, tooling validation, and production ergonomics", "Design a fixture and verify accessibility, repeatability, and manufacturing fit", ("Tool Design", "CAD", "Manufacturing Processes", "GD&T", "Design for Manufacturing", "Quality Engineering"), ("CNC Machining", "Automation")),
        ("Product Development Engineer", "user needs, concepts, prototypes, verification, and cross-functional release", "Build a product concept through requirements, prototype, and verification evidence", ("Product Development", "Mechanical Design", "CAD", "Design for Manufacturing", "Project Management", "Technical Writing"), ("Rapid Prototyping", "Finite Element Analysis")),
        ("Industrial Engineer", "work systems, flow, capacity, ergonomics, and measurable operational improvement", "Map a process, establish baseline metrics, and validate a small improvement", ("Industrial Engineering", "Operations Research", "Lean Manufacturing", "Data Analysis", "Project Management", "Quality Engineering"), ("Simulation", "Six Sigma")),
    ],
    "Civil Engineering": [
        ("Structural Engineer", "structural analysis, load paths, materials, and code-aware design review", "Analyze a small structure and show load assumptions, checks, and design drawings", ("Structural Analysis", "Structural Design", "Reinforced Concrete", "Steel Design", "Engineering Mechanics", "Structural Engineering Software"), ("ETABS", "Building Information Modeling")),
        ("Geotechnical Engineer", "site investigation, soil behavior, foundations, and ground-risk decisions", "Interpret a sample soil report and compare foundation options with assumptions", ("Geotechnical Engineering", "Soil Mechanics", "Foundation Engineering", "Engineering Geology", "Data Analysis", "Technical Writing"), ("Slope Stability", "PLAXIS")),
        ("Transportation Engineer", "traffic operations, geometric design, safety, and transport data", "Analyze a corridor problem and develop a safety-aware design recommendation", ("Transportation Engineering", "Traffic Engineering", "Surveying", "Data Analysis", "Civil CAD", "Engineering Design"), ("GIS", "Road Safety")),
        ("Construction Project Engineer", "scope, schedule, coordination, quality records, and field delivery", "Create a small project execution plan with schedule, risk, and quality checkpoints", ("Construction Management", "Project Management", "Quantity Surveying", "Technical Documentation", "Construction Safety", "BIM"), ("Primavera P6", "Contract Administration")),
        ("Site Engineer", "site coordination, setting out, material checks, work sequencing, and daily records", "Prepare a sample site method statement and inspection checklist for a work package", ("Site Engineering", "Surveying", "Construction Methods", "Construction Safety", "Quality Engineering", "Technical Documentation"), ("Civil CAD", "BIM")),
        ("Quantity Surveyor", "measurement, bills of quantities, cost plans, variations, and contract records", "Measure a small package and prepare a transparent bill of quantities", ("Quantity Surveying", "Construction Estimating", "Cost Engineering", "Excel", "Construction Management", "Contract Administration"), ("BIM", "Primavera P6")),
        ("BIM Coordinator", "model coordination, clash review, information standards, and design handover", "Coordinate a sample building model and publish an issue and handover log", ("Building Information Modeling", "Revit", "Civil CAD", "Technical Documentation", "Project Management", "Construction Methods"), ("Navisworks", "Digital Construction")),
        ("Water Resources Engineer", "hydrology, hydraulics, watershed data, and water infrastructure planning", "Build a catchment assessment and explain design assumptions and uncertainty", ("Water Resources Engineering", "Hydrology", "Hydraulics", "Data Analysis", "GIS", "Engineering Mathematics"), ("HEC-HMS", "Climate Resilience")),
        ("Environmental Civil Engineer", "environmental assessments, water and waste systems, mitigation, and monitoring", "Prepare an environmental baseline and a monitored mitigation plan for a sample site", ("Environmental Engineering", "Water Quality", "Environmental Impact Assessment", "GIS", "Data Analysis", "Technical Writing"), ("Wastewater Treatment", "Sustainability")),
        ("Transportation Planner", "travel demand, land use, network access, public transport, and equitable mobility", "Analyze a neighborhood mobility dataset and propose measurable improvements", ("Transportation Planning", "GIS", "Data Analysis", "Urban Planning", "Transportation Engineering", "Communication"), ("Public Transport", "Road Safety")),
        ("Civil Materials Engineer", "concrete, asphalt, aggregates, test methods, and materials quality", "Analyze sample test results and recommend a quality-control action", ("Civil Engineering Materials", "Concrete Technology", "Materials Testing", "Quality Engineering", "Data Analysis", "Technical Documentation"), ("Asphalt Technology", "Sustainability")),
        ("Land Surveyor", "control networks, field measurements, coordinate systems, and survey deliverables", "Produce a checked topographic survey workflow and annotated plan", ("Land Surveying", "Geospatial Analysis", "GIS", "Civil CAD", "Measurement and Instrumentation", "Technical Documentation"), ("GNSS Surveying", "Remote Sensing")),
        ("Urban Infrastructure Planner", "infrastructure systems, land use, service access, and capital planning", "Map an infrastructure gap and prepare an options comparison for a local area", ("Urban Planning", "Infrastructure Planning", "GIS", "Data Analysis", "Project Management", "Communication"), ("Transportation Planning", "Climate Resilience")),
        ("Construction Estimator", "quantity takeoffs, unit rates, bid assumptions, and cost-risk communication", "Prepare a traceable estimate with quantities, exclusions, and sensitivity notes", ("Construction Estimating", "Quantity Surveying", "Cost Engineering", "Excel", "Construction Methods", "Technical Writing"), ("BIM", "Contract Administration")),
        ("Infrastructure Asset Engineer", "asset condition, lifecycle risk, inspection data, and renewal prioritization", "Create an asset register and prioritize interventions using transparent criteria", ("Asset Management", "Infrastructure Planning", "Civil Engineering", "Data Analysis", "Risk Assessment", "Technical Documentation"), ("GIS", "Reliability Engineering")),
        ("Bridge Engineer", "bridge behavior, load rating, materials, inspection, and rehabilitation concepts", "Review a bridge case and deliver a load-path, inspection, and repair concept", ("Bridge Engineering", "Structural Analysis", "Structural Design", "Reinforced Concrete", "Steel Design", "Technical Documentation"), ("Finite Element Analysis", "Asset Management")),
        ("Construction Safety Engineer", "hazard identification, work controls, inspections, and safety learning", "Prepare a task risk assessment and site safety observation workflow", ("Construction Safety", "Risk Assessment", "Construction Management", "Technical Documentation", "Communication", "Engineering Ethics"), ("Incident Investigation", "Environmental Health and Safety")),
        ("Water Treatment Engineer", "treatment process selection, water quality, hydraulics, and operating evidence", "Develop a small treatment-train concept with a mass balance and monitoring plan", ("Water Treatment", "Water Quality", "Hydraulics", "Environmental Engineering", "Process Engineering", "Data Analysis"), ("Wastewater Treatment", "Process Safety")),
    ],
    "Chemical Engineering": [
        ("Process Engineer", "process flows, equipment sizing, operating windows, and continuous improvement", "Prepare a process-flow and material-balance package for a sample unit", ("Process Engineering", "Material and Energy Balances", "Thermodynamics", "Fluid Mechanics", "Heat Transfer", "Process Simulation"), ("Aspen Plus", "Process Control")),
        ("Chemical Production Engineer", "safe, consistent production, shift performance, process data, and loss reduction", "Analyze a production case and propose a safe, measurable throughput improvement", ("Chemical Process Operations", "Process Engineering", "Process Safety", "Statistical Process Control", "Data Analysis", "Troubleshooting"), ("Lean Manufacturing", "Process Control")),
        ("Process Safety Engineer", "hazard identification, safeguards, operating procedures, and incident learning", "Complete a small HAZOP-style review and track actions to closure", ("Process Safety", "HAZOP", "Risk Assessment", "Chemical Process Operations", "Technical Documentation", "Engineering Ethics"), ("Layer of Protection Analysis", "Environmental Health and Safety")),
        ("Biochemical Engineer", "bioreactors, biological process variables, scale-up, and product recovery", "Model a simple bioprocess and document yield, sterility, and scale assumptions", ("Biochemical Engineering", "Biotechnology", "Bioreactor Design", "Mass Transfer", "Data Analysis", "Process Engineering"), ("Downstream Processing", "Python")),
        ("Pharmaceutical Process Engineer", "formulation and manufacturing flows, validation, quality systems, and scale transfer", "Map a sample process with critical quality attributes and control points", ("Pharmaceutical Engineering", "Process Engineering", "Quality Assurance", "Process Validation", "Process Safety", "Technical Documentation"), ("Good Manufacturing Practice", "Biotechnology")),
        ("Energy Process Engineer", "energy conversion, process efficiency, heat integration, and emissions awareness", "Build an energy balance and prioritize efficiency changes with a payback estimate", ("Energy Systems", "Thermodynamics", "Heat Transfer", "Process Engineering", "Data Analysis", "Sustainability"), ("Renewable Energy", "Carbon Accounting")),
        ("Environmental Process Engineer", "pollution prevention, treatment processes, waste streams, and compliance evidence", "Create a waste-stream balance and treatment concept with measurable controls", ("Environmental Engineering", "Process Engineering", "Water Treatment", "Mass Transfer", "Environmental Impact Assessment", "Data Analysis"), ("Wastewater Treatment", "Sustainability")),
        ("Chemical Quality Engineer", "sampling plans, specifications, nonconformance, and process capability", "Analyze a sample quality dataset and prepare a corrective-action report", ("Quality Engineering", "Chemical Process Operations", "Statistical Process Control", "Analytical Chemistry", "Data Analysis", "Technical Documentation"), ("Six Sigma", "Quality Assurance")),
        ("Chemical Plant Design Engineer", "process selection, PFD/P&ID development, equipment arrangement, and design reviews", "Develop a conceptual plant package with a process flow and equipment list", ("Chemical Plant Design", "Process Engineering", "Process Simulation", "Piping and Instrumentation Diagrams", "Process Safety", "Project Management"), ("Aspen Plus", "HAZOP")),
        ("Polymer Process Engineer", "polymer properties, formulation, processing windows, and product performance", "Compare processing conditions and material properties for a polymer part", ("Polymer Engineering", "Materials Science", "Chemical Process Operations", "Thermodynamics", "Quality Engineering", "Data Analysis"), ("Rheology", "Materials Testing")),
        ("Food Process Engineer", "food process flows, heat treatment, hygiene, packaging, and quality controls", "Map a food process and justify critical quality and hygiene checkpoints", ("Food Engineering", "Food Safety", "Heat Transfer", "Process Engineering", "Quality Assurance", "Technical Documentation"), ("Biotechnology", "Packaging Engineering")),
        ("Petroleum Process Engineer", "hydrocarbon processing, separations, process control, and facility safety", "Create a simplified process-flow study with material balance and hazard notes", ("Petroleum Engineering", "Process Engineering", "Thermodynamics", "Fluid Mechanics", "Process Safety", "Process Simulation"), ("Piping and Instrumentation Diagrams", "Aspen Plus")),
        ("Water Treatment Process Engineer", "physical, chemical, and biological treatment operations and performance monitoring", "Size a treatment sequence at concept level and define its monitoring plan", ("Water Treatment", "Chemical Process Operations", "Mass Transfer", "Environmental Engineering", "Data Analysis", "Process Control"), ("Wastewater Treatment", "Process Simulation")),
        ("Chemical R&D Engineer", "experimental design, reaction or formulation studies, analysis, and reproducibility", "Design a small experiment and present a reproducible result with limitations", ("Research Methods", "Chemical Engineering", "Analytical Chemistry", "Data Analysis", "Experimental Design", "Technical Writing"), ("Python", "Materials Science")),
        ("Process Control Engineer", "instrumentation, dynamic response, controller tuning, and process stability", "Model and tune a process loop with disturbance and alarm-response scenarios", ("Process Control", "Control Systems", "Instrumentation Engineering", "MATLAB", "Process Engineering", "Data Analysis"), ("PLC Programming", "Process Simulation")),
        ("Chemical Scale-Up Engineer", "lab-to-pilot transfer, similarity, mixing, heat removal, and operating envelopes", "Prepare a scale-up basis with assumptions, risks, and validation experiments", ("Scale-Up Engineering", "Process Engineering", "Heat Transfer", "Fluid Mechanics", "Process Safety", "Experimental Design"), ("Biochemical Engineering", "Process Simulation")),
        ("Chemical Regulatory Affairs Engineer", "product and process documentation, technical standards, change control, and compliance", "Build a compliance evidence map for a sample process change", ("Regulatory Affairs", "Quality Assurance", "Chemical Process Operations", "Technical Documentation", "Risk Assessment", "Engineering Ethics"), ("Good Manufacturing Practice", "Environmental Health and Safety")),
        ("Chemical Applications Engineer", "customer process requirements, product selection, troubleshooting, and technical communication", "Turn a customer case into a technically checked process recommendation", ("Chemical Engineering", "Process Engineering", "Communication", "Problem Solving", "Technical Writing", "Customer Support"), ("Analytical Chemistry", "Project Management")),
    ],
}


def _slug(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", value.casefold())).strip()


def engineering_skill_names() -> list[str]:
    names: set[str] = set()
    for roles in ROLE_ROWS.values():
        names.update(roles[0][3])
        for _, _, _, required, preferred in roles:
            names.update(required)
            names.update(preferred)
    return sorted(names, key=str.casefold)


def branch_catalog() -> list[dict[str, Any]]:
    names = ["Computer Science & IT", *ROLE_ROWS]
    cse_count = len(json.loads((DATA / "jd_fixtures.json").read_text(encoding="utf-8")))
    records: list[dict[str, Any]] = []
    for name in names:
        metadata = BRANCHES[name]
        count = cse_count if name == "Computer Science & IT" else len(ROLE_ROWS[name])
        records.append({"name": name, "role_count": count, **metadata})
    return records


def _course_records(branch: str, focus: str) -> list[dict[str, str]]:
    metadata = BRANCHES[branch]
    course_search = f"{metadata['course_url']}?search={quote_plus(focus)}" if "nptel.ac.in" in metadata["course_url"] else metadata["course_url"]
    courses = [
        {
            "title": f"{focus.title()} course options",
            "provider": metadata["provider"],
            "url": course_search,
            "note": "Search current courses for this specialization. Check the syllabus and enrollment dates before choosing a course.",
        },
    ]
    for prefix in ("secondary", "tertiary"):
        if metadata.get(f"{prefix}_url"):
            courses.append({
                "title": str(metadata[f"{prefix}_course"]),
                "provider": str(metadata[f"{prefix}_provider"]),
                "url": str(metadata[f"{prefix}_url"]),
                "note": "Official learning materials for strengthening the tools and fundamentals used in this career path.",
            })
    return courses


def load_role_catalog() -> list[dict[str, Any]]:
    base_path = DATA / "jd_fixtures.json"
    base_records = json.loads(base_path.read_text(encoding="utf-8"))
    records: list[dict[str, Any]] = []
    for record in base_records:
        copied = dict(record)
        copied.setdefault("branch", "Computer Science & IT")
        records.append(copied)

    for branch, role_rows in ROLE_ROWS.items():
        metadata = BRANCHES[branch]
        for title, focus, project, required, preferred in role_rows:
            role = _slug(title)
            required_text = ", ".join(required)
            preferred_text = ", ".join(preferred)
            description = f"Apply {metadata['foundation'].lower()} to {focus}."
            records.append({
                "title": title,
                "role": role,
                "company": f"Sample {branch.split()[0]} Engineering",
                "location": "Remote / On-site",
                "branch": branch,
                "sector": branch,
                "description": description,
                "focus": focus,
                "project": project,
                "foundation": metadata["foundation"],
                "toolchain": metadata["toolchain"],
                "practice": metadata["practice"],
                "courses": _course_records(branch, focus),
                "required_skills": list(required),
                "preferred_skills": list(preferred),
                "text": f"{title}: {description} Required skills include {required_text}. Preferred: {preferred_text}.",
            })
    return records
