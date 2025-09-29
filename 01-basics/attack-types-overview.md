# Fault Injection — Attack Types 

> Purpose: for quick reading and practical understanding. Each section explains **how the attack works** (step-by-step), what to look for, and includes one short real-world example / reference to read next.

---

## Voltage glitching

**How it works — step by step**
1. Choose a *trigger* that reliably indicates the sensitive operation (GPIO toggle, serial packet, known instruction).  
2. Attach a controlled switching element (FET/crowbar) to the device Vcc rail or an internal Vcc net.  
3. Use the trigger to time a short voltage pulse (dip or spike) so it overlaps the target instruction or memory write.  
4. Observe device outputs or repeated runs; a successful glitch will cause an instruction skip, corrupted load/store, or altered branch.  
5. Collect multiple faulty outputs and correlate them to the original operation (useful for DFA on crypto).

**What to tune**
- Pulse timing relative to trigger (ns–µs resolution).  
- Pulse width and amplitude.  
- Number of repeated trials at each setting.

**Why it works**
Transient undervoltage/overvoltage changes transistor switching behavior and memory sense thresholds for a short time, producing deterministic faults when well-timed.

**Quick PoC pattern**
- Map where the sensitive code runs → add a trigger → sweep timing/amplitude → capture faulty ciphertexts or bypassed checks.

**Real-world example / reference**
ChipWhisperer labs and practical tutorials show voltage glitching on AES implementations and how to sweep timing/amplitude to force faulty outputs. 

---

## Clock glitching / frequency manipulation

**How it works — step by step**
1. Identify or gain access to the clock source (external crystal input, test point, or PLL output).  
2. Insert a clock injector/phase shifter or temporarily drive the clock line with a controllable source.  
3. Inject jitter, a short pause, or a phase error synchronized to the trigger so that a flip-flop samples at the wrong time.  
4. The CPU or logic unit mis-samples data or instructions, producing incorrect values or control-flow anomalies.  
5. Monitor behavior and iterate timing until a reproducible fault is found.

**What to tune**
- Exact phase relative to the target edge.  
- Pulse width and shape.  
- Which clock domain to disturb (core, bus, peripheral).

**Why it works**
Digital logic depends on setup/hold timing; violating timing windows makes registers capture incorrect values or instructions, causing skipped or corrupted operations.

**Quick PoC pattern**
- Probe clock → synchronize injection to trigger → sweep phase/delay → look for incorrect results or crashes.

**Real-world example / reference**
Clock-glitching is covered in practical labs and training chapters (voltage vs clock comparisons) and documented in ChipWhisperer and HSL/teaching materials.

---

## Electromagnetic (EM) fault injection

**How it works — step by step**
1. Use a near-field EM probe and position it close to the target chip area (often over the crypto core or bus lines).  
2. Synchronize a short EM pulse with the trigger for the sensitive operation.  
3. The pulse couples into on-die metal and transistors, causing local transient voltage/current changes that flip bits or upset logic.  
4. By sweeping probe position, timing, and pulse energy you can localize faults to small die regions.  
5. Correlate faulted outputs with probe position/time to identify exploitable effects.

**What to tune**
- Probe position (mm → sub-mm precision matters).  
- Pulse energy and duration.  
- Timing offset relative to trigger.

**Why it works**
EM fields couple into local wiring and gates; targeted pulses cause local charge/field disturbances that produce deterministic faults without needing to disturb global power.

**Quick PoC pattern**
- Decapsulate or remove shield if required → map likely die regions → sweep probe position & timing while issuing target op → capture and analyze faults.

**Real-world example / reference**
Practical EM fault injection characterizations show how EM pulses induce localized faults and discuss position/timing correlation in lab reports.

---

## Laser fault injection

**How it works — step by step**
1. Decapsulate the package or use a windowed package to expose the die or backside.  
2. Use microscope optics to identify die landmarks (crypto core, registers).  
3. Fire short, focused laser pulses at micron-scale locations while the target operation executes (triggered).  
4. The laser injects charge in a tiny region, flipping bits or corrupting specific gates/registers.  
5. Sweep location & timing to find a spot that produces reproducible faults (e.g., single-bit flips in a key register).

**What to tune**
- Laser pulse energy, duration, and focus spot size.  
- Exact die location and timing relative to trigger.

**Why it works**
Photon energy creates localized carriers or charge that upset transistor operation at specific cells — very high spatial precision yields powerful, targeted faults.

**Quick PoC pattern**
- Map die → align laser → trigger on sensitive operation → sweep location/timing → analyze single-bit faults for key recovery or bypass.

**Real-world example / reference**
Multiple reports (industry BSI and LLFI studies) demonstrate laser attacks on signature/verification code and XMSS verification as practical PoCs.

---

## Software / firmware faulting (non-physical)

**How it works — step by step**
1. Perform static analysis to find input parsers, update routines, or IPC endpoints.  
2. Fuzz or craft malformed inputs to trigger exceptions, buffer corruptions, or race conditions.  
3. Use emulators/debuggers to inject register/memory corruption at a chosen execution point (simulate transient faults).  
4. If a fault causes a logic skip, corruption, or unchecked state, escalate to exploit (e.g., skip auth, leak data).  
5. Combine with instrumentation to reproduce and harden against the fault.

**What to tune**
- Input vectors and fuzzing parameters.  
- Emulator injection timing and location.

**Why it works**
Higher-level code often lacks redundancy and can fail to handle unexpected states — faults here are cheap and can produce exploitable conditions without physical tools.

**Quick PoC pattern**
- Static analysis → targeted fuzzing → emulator-based bit flips or exception injections → validate bypass/exploit.

**Real-world example / reference**
Software/firmware faulting is commonly covered in security training and is the usual first step; ChipWhisperer/teaching resources and academic reviews highlight software faulting as lower-cost reconnaissance before physical attacks.

---

## Power-analysis-assisted faulting (combined attacks)

**How it works — step by step**
1. Capture power traces of the target operation to build a timing/template of internal events (e.g., round boundaries in AES).  
2. Use the trace to identify a reliable, high-resolution trigger point (when the sensitive operation is active).  
3. Inject a fault (voltage/EM/laser) precisely at the desired trace offset using the trigger derived from power analysis.  
4. Collect correct + faulty outputs; apply DFA or hybrid analysis to recover keys faster than with blind faulting.

**What to tune**
- Trace alignment & averaging.  
- Fault injection timing relative to power-trace features.  
- Number of faulty outputs required for DFA.

**Why it works**
Power traces reveal internal timing; combining that with faulting narrows the timing window and dramatically increases success/reproducibility, making key extraction feasible with fewer faults.

**Quick PoC pattern**
- Trace → locate operation boundary → trigger+inject → collect correct/faulty pairs → apply DFA.

**Real-world example / reference**
Academic and practical work documents DFA combined with side-channel templates; training chapters and the Barenghi survey describe combined SPA+DFA approaches.

---

## Short further-reading

- ChipWhisperer tutorials — practical voltage-glitch labs and step-by-step PoCs.
- Laser/LLFI practical studies — examples of laser attacks on signature verification.

