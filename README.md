# Fault Injection Evaluation — Methodology Study

Simulations, analysis methods and a sample evaluation report, built to work through how a fault-injection evaluation is planned, run, measured and reported.

## Background

I trained as an electronic engineer and spent two years in regulated explosives manufacturing. Part of that job was injecting controlled faults into instrumentation loops (4–20 mA current and voltage injection) to check that sensors responded correctly and that the system failed safe. I also documented how voltage fluctuation and electromagnetic interference showed up in system behaviour.

That was fault-condition testing for safety. This repository asks the security version of the same question: what an attacker gains by pushing a device outside its operating conditions on purpose, and how an evaluator measures and reports it. The work here is simulation-based. It doesn't include glitching real silicon.

## What's here

**1. Fundamentals**
- Fault-injection principles and an attack taxonomy: voltage, clock, EM and laser
- Real-world impact: why fault-injection evaluation matters

**2. Simulations** (Python, NumPy, Matplotlib, Jupyter)
- **PIN-bypass simulator:** how a timing-window fault skips an authentication check
- **Glitch parameter sweep:** glitch width and offset against success rate, i.e. the structured search an evaluator runs instead of random attempts
- **AES differential fault analysis:** recovering key material from faulty ciphertexts

**3. Bench concepts**
- Arduino-based voltage-glitch controller (design concept)
- Python automation for iterative test runs
- Notes on evaluation-lab setup requirements

**4. Analysis and reporting**
- **Sample evaluation report**, structured as a lab would deliver one
- **Statistical analysis**, separating true fault effects from noise
- **Countermeasure assessment**, judging whether a protection held

## Method

Four things run through every part of this repository:
- **Structured parameter exploration**, not random attempts
- **Identifying vulnerable code patterns and timing windows**
- **Statistical rigour** to tell a real effect from noise
- **Reporting** that a third party can follow and reproduce

## Next steps

- Move from simulation to hardware: ChipWhisperer-Lite and the voltage-glitch tutorials on a real target
- EM fault injection theory
- ISO/IEC 17825 (testing methods for non-invasive attack mitigation)

## Tools

Python, C/Arduino, NumPy, Matplotlib, Jupyter

## Contact

Hafizzuddin Hashim · hafizzuddinfahmi@gmail.com · linkedin.com/in/hafizzuddin-hashim · Kuala Lumpur, Malaysia
