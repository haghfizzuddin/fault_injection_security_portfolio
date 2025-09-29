# Fault Injection — Theory

## What it is  
**Fault injection** is the deliberate introduction of abnormal physical or logical disturbances into a system to induce incorrect behavior and reveal vulnerabilities. It is used as both an evaluation technique (to test resilience, compliance, and countermeasures) and as an attacker method (to extract secrets or bypass checks).In cybersecurity and hardware security contexts, it is particularly relevant for evaluating the resilience of embedded devices, cryptographic implementations, and secure elements against physical and logical tampering attacks.

## Core idea and Concept 
Fault injection operates on the assumption that:

1. Modern devices have deterministic execution paths.
2. Introducing faults at precise times can alter program flow or data values.
3. These faults can be reproducible, allowing systematic testing.

It creates a controlled, reproducible fault at a precise time/place to alter program flow or data values so the system leaks information or skips security checks.

The theory behind fault injection is based on the idea that abnormal conditions—such as voltage glitches, clock manipulations, electromagnetic interference, or software exceptions—may force a system to deviate from its intended operation. By carefully crafting these disturbances, attackers or evaluators can cause the system to reveal secret data, bypass authentication, or skip critical security checks.

## Types of fault injection
- **Voltage glitching** — brief dips/spikes on supply rails to cause instruction/data corruption.  
- **Clock glitching / frequency manipulation** — disturb clock to create timing violations.  
- **Electromagnetic (EM) injection** — induce faults with EM pulses near circuitry.  
- **Laser fault injection** — localized charge disruption by targeting die areas (highly precise).  
- **Power analysis-assisted faulting** — combine side-channel leakage with faults to time attacks.  
- **Microprobing / invasive attacks** — physical access to buses/pins after decapping.  
- **Software/firmware fault injection** — malformed inputs, exception forcing, or faulting simulation at higher layers.  
- **Environmental abuse** — temperature, radiation, or vibration to trigger failure modes.

## Typical target assets (what attackers try to break)
- **Cryptographic keys and operations** (AES, RSA, ECC) — Differential Fault Analysis (DFA) is common.  
- **Secure boot / firmware integrity checks** — skip or modify signature verification.  
- **Authentication logic / PIN checks** — bypass PIN/password checks or authorization gates.  
- **Access control and privilege checks** — force logic to mis-evaluate conditionals.  
- **Hardware-protected elements** (TPM, secure element, smartcard) — extract secrets or bypass protections.  
- **State machines and rollback protections** — corrupt state to reach an insecure state.

## Applications
Fault injection is widely used for:

* Security evaluation of smart cards and secure elements
* Cryptographic analysis, e.g., Differential Fault Analysis (DFA) on AES or RSA
* Testing system resilience under abnormal operating conditions
* Certification processes in Common Criteria (CC) and EMVCo evaluations

## Security Implications

While primarily used in laboratory and certification environments, the same techniques are available to attackers with sufficient resources. Successful fault injection attacks may lead to:

* Extraction of cryptographic keys
* Circumvention of secure boot or firmware integrity checks
* Privilege escalation or bypass of authentication

## Attack assets (what attackers/evaluators need)
- **Equipment:** glitcher modules, high-speed power supplies, clock manipulators, EM probes/pulsers, pulsed lasers and optics, microscopes & decapping tools, oscilloscopes, logic analyzers.  
- **Trigger & instrumentation:** precise trigger signals (GPIO, protocol traces), high-sample-rate oscilloscope, and data capture to correlate fault to code location.  
- **Platform knowledge:** schematics/pinouts, protocol timings, firmware layout, debug vectors, instruction timing.  
- **Software tooling:** emulators/simulators, differential analysis scripts, and DFA tooling.

## How countermeasures work 
Countermeasures aim to **detect, tolerate, or make exploitation impractical**.

### Detection & hardening
- **Redundant computation / temporal redundancy:** repeat operations and compare results.  
- **Control-flow integrity & checksums:** insert control-flow or CRC/HMAC checks to detect unexpected jumps or corrupted code.  
- **Error-detecting codes:** parity, CRCs, ECC on critical registers/memory.  
- **Sensors & tamper detection:** voltage/clock/temperature/EM sensors that trigger safe-fail or key erase.  
- **Physical shielding / active meshes:** metal meshes or active tamper layers to block EM/laser attacks.  
- **Hardened logic / dual-rail circuits:** reduce impact of single transient faults.  
- **Constant-time, masked crypto & redundancy:** masking, recomputation, and algorithm-level checks reduce DFA effectiveness.  
- **Nonce/operation verification:** require external verification or signatures for sensitive state changes.

### Tolerance / mitigation
- **Fail-safe behavior:** default to deny/lock when faults are detected.  
- **Diversity & randomization:** randomize timing/addresses or use multiple algorithm variants.  
- **Active monitoring & logging:** detect repeated unusual conditions and restrict or lock the device.

## Practical considerations for evaluation
- **Fault model matters:** evaluate against realistic amplitudes, timing windows, and spatial resolution.  
- **Reproducibility:** faults must be reproducible and correlatable to code.  
- **Cost vs. benefit:** laser & invasive attacks are expensive — threat model must justify them.  
- **Layered defense:** combine hardware sensors, secure coding, and crypto-level checks — no single countermeasure is sufficient.

## References
1. Skorobogatov, S. *Semi-invasive attacks — A new approach to hardware security analysis.* Univ. of Cambridge tech report, 2005.  
2. Barenghi, A., Bertoni, G., Breveglieri, L., & Pelosi, G. *Fault Injection Attacks on Cryptographic Devices: Theory, Practice, and Countermeasures.* Proceedings of the IEEE, 2012.  
3. Boneh, D., DeMillo, R., & Lipton, R. *On the importance of checking cryptographic protocols against fault attacks.* 1997.
