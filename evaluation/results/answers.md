# Every answer

## q01 (en, typos): My pump makes a lot of noize and vibrats when its on

*Expected:* Noise: the only cause in the table is the pump not being secured.

### `qwen` · 102 s

*intent* troubleshooting · *language* en · *verified* True · *causes* Pump incorrectly secured

> The noise and vibration when the pump is on are likely caused by the pump being incorrectly secured (high). Secure the pump correctly [p. 13].
> 
> **Safety:** before any electrical or mechanical work, disconnect the pump from the mains, block all start-up devices, check there is no voltage and wait for the impeller to stop completely [p. 8]. Electrical work must be done by qualified personnel [p. 5].

### `llama` · 309 s · failed: intent, cause_found, top_cause

*intent* safety · *language* en · *verified* True

> Here are the likely causes and fixes for the noise and vibration of the pump:
> 
> 1. **Pump incorrectly secured**: Secure the pump correctly. [p. 13]
> 2. **Motor blocked**: Remove the motor and contact the technical service. [p. 13]
> 3. **Increased temperature in the terminal box**: Check the junction box connections. [p. 13]
> 4. **Thermal protection trips**: Connect the cables correctly to the junction boxes. [p. 13]
> 
> **Safety:** before any electrical or mechanical work, disconnect the pump from the mains, block all start-up devices, check there is no voltage and wait for the impeller to stop completely [p. 8]. Electrical work must be done by qualified personnel [p. 5].

### `gemma` · 278 s

*intent* troubleshooting · *language* en · *verified* True · *causes* Pump incorrectly secured

> 1. Secure the pump correctly [p. 13].
> 2. Check for machine vibrations. In the event of a fault, stop the machine immediately and contact the nearest Technical Assistance Service [p. 8].
> 
> **Safety:** before any electrical or mechanical work, disconnect the pump from the mains, block all start-up devices, check there is no voltage and wait for the impeller to stop completely [p. 8]. Electrical work must be done by qualified personnel [p. 5].

### `deepseek` · 225 s · failed: top_cause

*intent* troubleshooting · *language* en · *verified* True · *causes* Load loss in the installation; Pump incorrectly secured

> 1. Check if the pump is correctly secured to the base or mounting surface. If it's not, secure it correctly according to the manufacturer's instructions [p. 13].
> 2. Ensure the installation is properly set up, with no load loss that could cause vibration. Check for any obstructions or misaligned parts that might be causing the noise and vibration [p. 13].
> 
> Safety: Before any mechanical checks, ensure the pump is disconnected from the mains and there is no voltage present [p. 8].
> 
> **Safety:** before any electrical or mechanical work, disconnect the pump from the mains, block all start-up devices, check there is no voltage and wait for the impeller to stop completely [p. 8]. Electrical work must be done by qualified personnel [p. 5].

### `auto` · 33 s

*intent* troubleshooting · *language* en · *verified* True · *causes* Pump incorrectly secured

> The likely cause of the noise and vibration when the pump is on is that the pump is incorrectly secured [p. 13]. Secure the pump correctly to resolve the issue.
> 
> **Safety:** before any electrical or mechanical work, disconnect the pump from the mains, block all start-up devices, check there is no voltage and wait for the impeller to stop completely [p. 8]. Electrical work must be done by qualified personnel [p. 5].

### `offline` · <0.1 s · failed: cause_found, top_cause

*intent* troubleshooting · *language* en · *verified* True

> From the ASTRAL Pool manual:
> - **7. Troubleshooting:** Symptoms: The pump makes a noise. Cause: Pump incorrectly secured. Solution: Secure the pump correctly. [p. 13]
> - **3. Installation And Assembly > Location:** - Fit the pump below the water level in the pool to improve pump performance. - Make sure that the pump is safe from possible flooding and receives dry ventilation. [p. 9]
> - **2. General Safety Regulations > Warnings During Installation And Assembly Work:** - In cases of junction box connections only: when connecting the electrical wiring to the motor, check the layout inside the connection box and make sure there are no pieces of wiring inside after it has been closed and that the grounding conductor is correctly con - nected. Connect the motor in line with the wiring diagram attached to the machine. - In cases of junction box connections only: make sure that the electrical wiring connections ... [p. 7]
> 
> **Safety:** before any electrical or mechanical work, disconnect the pump from the mains, block all start-up devices, check there is no voltage and wait for the impeller to stop completely [p. 8]. Electrical work must be done by qualified personnel [p. 5].

## q02 (es, clean): La bomba no ceba y sale muy poca agua, ¿qué puede ser?

*Expected:* Not primed + small flow: the three rows that share both symptoms.

### `qwen` · 103 s · failed: facts

*intent* troubleshooting · *language* es · *verified* True · *causes* Motor turning in wrong direction; Pre-filter blocked

> Las causas posibles son:
> 1. La pre-filtro está bloqueado (medio) -> Limpia el filtro [p. 13]
> 2. La bomba está girando en la dirección incorrecta (alta) -> Invert 2 fases de la corriente de alimentación [p. 13]
> 
> **Safety:** antes de cualquier trabajo eléctrico o mecánico, desconecte la bomba de la corriente de alimentación, bloquee todos los dispositivos de arranque, verifique si hay voltaje y espere hasta que la hélice pare completamente [p. 8]. Los trabajos eléctricos deben hacerse por personas calificadas [p. 5].

### `llama` · 198 s · failed: cause_found, top_cause, facts

*intent* troubleshooting · *language* es · *verified* True · *causes* Pre-filter blocked; Load loss in the installation

> Aquí tienes las posibles causas y soluciones:
> 
> 1. **Pre-filtro bloqueado (alto)**: Limpia el filtro [p. 13].
> 2. **Perdida de carga en la instalación (alta)**: Evita que los componentes causen pérdida de carga donde sea posible [p. 13].
> 
> **Safety:** Antes de realizar cualquier trabajo eléctrico o mecánico, desconecta la bomba de la red, bloquea todos los dispositivos de arranque, verifica que no haya voltaje y espera a que el impellor se detenga completamente [p. 8]. El trabajo eléctrico debe ser realizado por personal calificado [p. 5].

### `gemma` · 174 s · failed: top_cause

*intent* troubleshooting · *language* es · *verified* True · *causes* Pre-filter blocked; Motor turning in wrong direction; Air entering the suction pipe

> 1.  El pre-filtro está obstruido. Limpie el filtro [p. 13].
> 2.  El motor gira en la dirección incorrecta. Inverta 2 fases de alimentación [p. 13].
> 3.  Está entrando aire en la tubería de succion. Compruebe el estado de las conexiones y sellos de la tubería de succion [p. 13].
> 
> **Safety:** before any electrical or mechanical work, disconnect the pump from the mains, block all start-up devices, check there is no voltage and wait for the impeller to stop completely [p. 8]. Electrical work must be done by qualified personnel [p. 5].

### `deepseek` · 145 s · failed: facts

*intent* troubleshooting · *language* es · *verified* True · *causes* Wrong voltage; Motor turning in wrong direction; Filter cap badly sealed; Pre-filter blocked; Load loss in the installation; Pump incorrectly secured

> 1. Comprueba que la tensión de la red eléctrica sea la correcta según la placa de características del motor [p. 13].
> 2. Asegúrate de que el motor esté girando en el sentido correcto [p. 13]. Si no, invierte las dos fases de potencia [p. 13].
> 3. Limpia y verifica la condición de la cremallera del filtro [p. 13].
> 4. Limpia el pre-filtro [p. 13].
> 5. Verifica que no haya pérdidas de carga en la instalación [p. 13].
> 6. Asegúrate de que el tanque de la bomba esté correctamente asegurado [p. 13].
> 
> Si las causas mencionadas no resuelven el problema, considera que puede ser necesario consultar al Servicio de Asistencia Técnica.

### `auto` · 79 s · failed: page_cited, facts

*intent* troubleshooting · *language* es · *verified* True · *causes* Air entering the suction pipe; Motor turning in wrong direction; Wrong voltage; Pre-filter blocked; Load loss in the installation

> 1. Verifique que la toma de agua del filtro esté correctamente conectada y sin daños.
> 2. Compruebe que la tensión de alimentación está correcta en relación con la tensión de la placa de calibración.
> 3. Verifique que el motor esté girando en la dirección correcta. Si no lo está, inverte los dos fases de alimentación.
> 4. Limpie el filtro para asegurar que no esté obstruido.
> 5. Asegúrese de que no haya pérdidas de carga en la instalación.
> 
> **Safety:** antes de cualquier trabajo eléctrico o mecánico, desconecte la bomba de las líneas de alimentación, bloquee todos los dispositivos de arranque y asegúrese de que no haya tensión. Espere hasta que el impulsor de la bomba deje de girar completamente [p. 8]. El trabajo eléctrico debe ser realizado por personal calificado [p. 5].

### `offline` · <0.1 s · failed: intent, answer_language, cause_found, top_cause, page_cited, citations_valid, facts

*intent* general · *language* es · *verified* True

> I could not find this in the available product manuals. Please contact the nearest Technical Assistance Service.

## q03 (ca, missing accents): El motor s'ha aturat i crec que salta la proteccio termica

*Expected:* Motor stopped: junction box causes. Electrical work, so the disconnect warning is required.

### `qwen` · 127 s · failed: language, top_cause

*intent* troubleshooting · *language* es · *verified* True · *causes* Pump incorrectly secured; Motor blocked; The thermal protection trips

> 1. El motor ha saltat la protecció térmica (alta).
>    - Solució: Connectar les cables correctament als boxes de juntes [p. 13].
>    - **Safety:** Antes de qualsevol treball electrotècnic o mecànic, desconectar el motor dels mòvells, bloquejar tots els dispositius de començament i esperar que l'impèrfor sigui completament en calma [p. 8]. El treball electrotècnic ha de ser fet per persones qualificades [p. 5].

### `llama` · 169 s · failed: intent, language, cause_found, top_cause

*intent* safety · *language* es · *verified* True

> La següent causa és probable:
> 
> 1. Ajusta la mida del cable correctament a la connexió del box de connexió [p. 13].
> 2. Verifica que les connexions del cable estan correctes als boxs de connexió [p. 13].
> 
> **Safety:** Antes de fer qualsevol treball electrònic o mecànic sobre l'equipament, desconecta el motor de la màsterra, bloqueja tots els dispositius de inici, verifica que no hi ha tensió i espera que l'impeller estigui parat completament [p. 8]. El treball electrònic o mecànic requera personal qualificat [p. 5].

### `gemma` · 157 s · failed: language, answer_language

*intent* troubleshooting · *language* fr · *verified* True · *causes* The thermal protection trips

> 1. La protection thermique a déclenché en raison d'un arc électrique dans la boîte de jonction. Vérifiez les connexions de la boîte de jonction [p. 13].
> 2. La protection thermique a déclenché en raison d'une connexion incorrecte de la boîte de jonction. Serrez correctement le câble à la boîte de jonction / Adaptez la taille de la connexion du câble à la boîte de jonction [p. 13].
> 
> **Safety:** before any electrical or mechanical work, disconnect the pump from the mains, block all start-up devices, check there is no voltage and wait for the impeller to stop completely [p. 8]. Electrical work must be done by qualified personnel [p. 5].

### `deepseek` · 101 s · failed: intent, answer_language, cause_found, top_cause

*intent* start_up · *language* ca · *verified* True

> 1. Check the electric protection devices on the motor to ensure they are correctly calibrated and the protection against electrical and mechanical contacts is secure. [p. 7]
> 2. Check the temperature of the machine and the electric motor. If the temperature is high, stop the machine immediately and contact the nearest Technical Assistance Service. [p. 8]
> 3. Check for machine vibrations. If vibrations are present, stop the machine immediately and contact the nearest Technical Assistance Service. [p. 8]
> 4. If the motor has stopped due to increased temperature in the terminal box due to an electric arc, check the junction box connections. [p. 13]
> 5. If the motor has stopped due to the thermal protection tripping, ensure the cables are correctly connected to the junction boxes. [p. 13]
> 
> **Safety:** before any electrical or mechanical work, disconnect the pump from the mains, block all start-up devices, check there is no voltage and wait for the impeller to stop completely [p. 8]. Electrical work must be done by qualified personnel [p. 5].

### `auto` · 30 s · failed: language, answer_language, cause_found, top_cause, facts

*intent* troubleshooting · *language* es · *verified* True · *causes* Motor blocked

> 1. El motor está bloqueado.
> 2. Contactar con el servicio técnico [p. 13].
> 
> **Safety:** antes de cualquier trabajo eléctrico, desconecte el motor de las líneas de alimentación, bloquee todos los dispositivos de arranque y espere a que la hélice pare completamente [p. 8]. Los trabajos eléctricos deben hacerse por personas calificadas [p. 5].

### `offline` · <0.1 s · failed: intent, language, answer_language, cause_found, top_cause, page_cited

*intent* general · *language* es · *verified* True

> From the ASTRAL Pool manual:
> - **6. Removal:** - The motor unit can be removed from the pump body without having to disconnect the pump's suction and return pipes. - To remove the motor unit from the pump body, remove the screws that join them together. [p. 12]
> - **3. Installation And Assembly > Electrical Installation:** ... - Use a rigid cable to connect the pump to the mains. If you use a flexible cable to connect it to the mains, it must have cable lugs to connect it to the terminals of the pump's motor. [p. 9]
> - **3. Installation And Assembly > Electrical Installation:** - Adjust the value of the ground fault circuit interrupter in line with pump intensity. - Before connecting the motor, check the type of fuse required. - Check the layout and connection of the earthing cable in the unit. - Respect the electrical installation and connection instructions. Failure to do so may lead to the pump's manufacturer declining all liability and rendering the warranty null and void. ... [p. 10]

## q04 (es, no accents or punctuation): mi bomba no arranca que tengo que revisar

*Expected:* Will not start: wrong voltage is the only row. Checking voltage is electrical work.

### `qwen` · 322 s · failed: cause_found, top_cause, facts

*intent* troubleshooting · *language* es · *verified* True · *causes* Motor turning in wrong direction; The thermal protection trips

> 1. La bomba no arranca. Las causas posibles son:
>    a) La protección térmica ha tripado (mediana) -> Conecte correctamente las cables a las cajas de conexión [p. 13].
>    b) La bomba está girando en el sentido incorrecto (alta) -> Invertir las dos fases de alimentación [p. 13].
> 
> Según la información del manual, la primera causa es la protección térmica que ha tripado. Para solucionar esto, se debe conectar correctamente las cables a las cajas de conexión. Esto se puede hacer siguiendo las instrucciones en la página 13 del manual.
> 
> Después de realizar la conexión correcta, si la bomba sigue sin arrancar, la segunda causa sería que la bomba está girando en el sentido incorrecto. Para solucionar esto, se debe invertir las dos fases de alimentación. Esto también se puede hacer siguiendo las instrucciones en la página 13 del manual.
> 
> **Safety:** antes de cualquier trabajo eléctrico o mecánico, desconecte la bomba de la red, bloquee todos los dispositivos de arranque, verifique que no haya voltaje y espere hasta que el impulsor pare completamente [p. 8]. Los trabajos eléctricos deben ser realizados por personal calificado [p. 5].

### `llama` · 234 s · failed: intent, cause_found, top_cause, page_cited

*intent* start_up · *language* es · *verified* True

> Aquí te presento los posibles problemas y soluciones para tu bomba:
> 
> 1. **Motor girando en la dirección equivocada**: Invierte 2 fases de energía.
> 2. **Voltage incorrecta**: Verifica la tensión en la placa de especificaciones y la de la red.
> 3. **Pre-filtro bloqueado**: Limpia el filtro.
> 4. **Pérdida de carga en la instalación**: Asegúrate de que los componentes no estén causando pérdida de carga en la instalación.
> 
> **Safety:** Antes de realizar cualquier trabajo eléctrico o mecánico, desconecta la bomba de la red, bloquea todos los dispositivos de arranque, verifica que no haya tensión y espera a que el impellor se detenga completamente [p. 8]. El trabajo eléctrico debe ser realizado por personal calificado [p. 5].

### `gemma` · 224 s

*intent* troubleshooting · *language* es · *verified* True · *causes* Wrong voltage; Pre-filter blocked; Motor blocked

> Para solucionar el problema de que la bomba no arranca, siga estos pasos:
> 
> 1.  Verifique la tensión en la placa de calificación y la tensión de la red eléctrica. Esto podría ser un error de tensión (alta) [p. 13].
> 2.  Limpie el filtro pre-filtro [p. 13].
> 3.  Si la bomba no arranca, retire el motor y póngase en contacto con el servicio técnico [p. 13].
> 
> **Safety:** before any electrical or mechanical work, disconnect the pump from the mains, block all start-up devices, check there is no voltage and wait for the impeller to stop completely [p. 8]. Electrical work must be done by qualified personnel [p. 5].

### `deepseek` · 327 s · failed: page_cited, citations_valid

*intent* troubleshooting · *language* es · *verified* True · *causes* Wrong voltage; Motor turning in wrong direction; Filter cap badly sealed

> 1. Verifica el voltaje en la placa de calificación y el de la red eléctrica.
> 2. Inverte 2 fases de potencia.
> 3. Limpia el casquillo de la filtración y verifica la condición de la silicona.
> 
> Safety: Antes de cualquier trabajo eléctrico o mecánico, desconécte la bomba de la red eléctrica, bloqueie todos los dispositivos de arranque y verifique que no haya tensión antes de comenzar.
> 
> **Safety:** antes de cualquier trabajo eléctrico o mecánico, desconecte la bomba de la red eléctrica, bloque todo el dispositivo de arranque, verifique que no haya tensión y espere a que el impulsor se detenga completamente antes de comenzar.

### `auto` · 119 s

*intent* troubleshooting · *language* es · *verified* True · *causes* Wrong voltage

> Las causas posibles son las siguientes:
> 
> 1. La tensión eléctrica está alta (wrong voltage) -> Compruebe la tensión en la etiqueta de calibración y que de la red de alimentación [p. 13].
> 
> Después de identificar la causa, siga estos pasos:
> 
> 1. Compruebe la tensión en la etiqueta de calibración y que de la red de alimentación [p. 13].
> 2. Si la tensión está correcta, revise la instalación eléctrica y asegúrese de que el motor está correctamente conectado y protegido contra contactos eléctricos y mecánicos [p. 7].
> 3. Si el motor está bloqueado, retire el motor y contacte al servicio técnico [p. 13].
> 
> **Safety:** antes de cualquier trabajo eléctrico o mecánico, desconecte la bomba de la red, bloquee todos los dispositivos de arranque y espere hasta que el impulsor pare completamente [p. 8]. Los trabajos eléctricos deben hacerse por personal calificado [p. 5].

### `offline` · <0.1 s · failed: answer_language, facts

*intent* troubleshooting · *language* es · *verified* True · *causes* Wrong voltage

> **Reported symptoms:** The pump will not start.
> 
> **Likely causes:**
> 1. **Wrong voltage** (high): Check the voltage on the rating plate and that of the mains [p. 13]
> 
> **Check first:** Check the voltage on the rating plate and that of the mains.
> 
> **Safety:** before any electrical or mechanical work, disconnect the pump from the mains, block all start-up devices, check there is no voltage and wait for the impeller to stop completely [p. 8]. Electrical work must be done by qualified personnel [p. 5].

## q05 (en, clean): The motor hums but the pump won't start. What should I do?

*Expected:* Hums but won't start: motor blocked, remove the motor and call the technical service.

### `qwen` · 111 s · failed: top_cause

*intent* troubleshooting · *language* en · *verified* True · *causes* Pump incorrectly secured; Motor blocked

> The motor hums but the pump won't start. The likely causes are:
> 1. Motor blocked (high) -> Remove the motor and contact the technical service [p. 13]
> 
> Fix these problems:
> 1. Ensure the power is disconnected before attempting to remove the motor. [p. 8]

### `llama` · 151 s

*intent* troubleshooting · *language* en · *verified* True · *causes* Motor blocked; Increased temperature in the terminal box due to electric arc; The thermal protection trips; Incorrect junction box connections

> Here are the likely causes and fixes:
> 
> 1. **Incorrect junction box connections (medium)**: 
>    - Check the junction box connections.
>    - Tighten the cable correctly to the junction box / Adapt the size of the cable connection to the junction box [p. 13]
> 
> 2. **Increased temperature in the terminal box due to electric arc (medium)**: 
>    - Check the junction box connections [p. 13]
> 
> 3. **Motor blocked (low)**: 
>    - Remove the motor and contact the technical service [p. 13]
> 
> 4. **The thermal protection trips (high)**: 
>    - Connect the cables correctly to the junction boxes [p. 13]
> 
> **Safety:** before any electrical or mechanical work, disconnect the pump from the mains, block all start-up devices, check there is no voltage and wait for the impeller to stop completely [p. 8]. Electrical work must be done by qualified personnel [p. 5].

### `gemma` · 302 s · failed: top_cause

*intent* troubleshooting · *language* en · *verified* True · *causes* Wrong voltage; Motor blocked; Pre-filter blocked

> 1. Check the voltage on the rating plate and that of the mains [p. 13].
> 2. Pre-filter blocked [p. 13]. Clean the filter.
> 3. Motor blocked [p. 13]. Contact the technical service.
> 
> **Safety:** before any electrical or mechanical work, disconnect the pump from the mains, block all start-up devices, check there is no voltage and wait for the impeller to stop completely [p. 8]. Electrical work must be done by qualified personnel [p. 5].

### `deepseek` · 204 s · failed: cause_found, top_cause, facts

*intent* troubleshooting · *language* en · *verified* True · *causes* Motor turning in wrong direction; Wrong voltage; Increased temperature in the terminal box due to electric arc; The thermal protection trips

> 1. Check if the motor is turning in the correct direction. If not, invert 2 power phases as per [p. 13].
> 2. Verify the voltage on the pump's rating plate and the mains voltage. If the voltage is incorrect, adjust to match the pump's requirements [p. 13].
> 3. Inspect the terminal box for any signs of increased temperature due to electric arcs. If found, check the junction box connections and ensure they are secure [p. 13].
> 4. If the thermal protection trips, ensure the cables are correctly connected to the junction boxes [p. 13].
> 
> Safety: Before performing any electrical work, disconnect the pump from the mains, block all start-up devices, check for voltage, and wait for the impeller to stop completely [p. 8]. Electrical work must be done by qualified personnel [p. 5].

### `auto` · 66 s

*intent* troubleshooting · *language* en · *verified* True · *causes* Motor blocked

> The motor hums but the pump won't start. The likely cause is a motor blocked (high). The solution is to remove the motor and contact the technical service [p. 13].
> 
> **Safety:** before any electrical or mechanical work, disconnect the pump from the mains, block all start-up devices, check there is no voltage and wait for the impeller to stop completely [p. 8]. Electrical work must be done by qualified personnel [p. 5].

### `offline` · <0.1 s

*intent* troubleshooting · *language* en · *verified* True · *causes* Motor blocked

> **Reported symptoms:** The motor is making a noise but will not start.
> 
> **Likely causes:**
> 1. **Motor blocked** (high): Remove the motor and contact the technical service [p. 13]
> 
> **Check first:** Remove the motor and contact the technical service.
> 
> **Safety:** before any electrical or mechanical work, disconnect the pump from the mains, block all start-up devices, check there is no voltage and wait for the impeller to stop completely [p. 8]. Electrical work must be done by qualified personnel [p. 5].

## q06 (de, clean): Wie oft muss man die Gleitringdichtung und die Lager wechseln?

*Expected:* Mechanical seal and bearings: every year (replacement table, p. 12).

### `qwen` · 19 s · failed: scope, intent, answer_language, page_cited, citations_valid, facts

*intent* out_of_scope · *language* de · *verified* True

> I can only help with technical questions about installing, starting up, maintaining and troubleshooting the pool equipment covered by the product manuals.

### `llama` · 99 s

*intent* maintenance · *language* de · *verified* True

> Die Gleitringdichtung und die Lager müssen alle 1 Jahr ersetzt werden. [p. 12]
> 
> **Safety:** Bevor Sie mit elektrischen oder mechanischen Arbeiten am Gerät beginnen, sollten Sie den Pumpe von der Stromversorgung trennen, alle Start-geräte blockieren, sicherstellen, dass keine Spannung vorhanden ist und auf ein vollständiges Stillstand der Impeller warten. Elektrische Arbeiten müssen von qualifizierten Fachkräften durchgeführt werden. [p. 8]

### `gemma` · 178 s · failed: intent

*intent* troubleshooting · *language* de · *verified* True · *causes* Filter cap badly sealed; Motor turning in wrong direction

> Die Gleitringdichtung und die Lager müssen jährlich gewechselt werden [p. 12]. Die O-Ringe und anderen Dichtkomponenten sollten ebenfalls jährlich ersetzt werden [p. 12].  Es wird empfohlen, die Dichtungen und Dichtkomponenten zu ersetzen, wenn die mechanische Dichtung und/oder die Lager ausgetauscht werden [p. 12].
> 
> **Safety:** before any electrical or mechanical work, disconnect the pump from the mains, block all start-up devices, check there is no voltage and wait for the impeller to stop completely [p. 8]. Electrical work must be done by qualified personnel [p. 5].

### `deepseek` · 123 s · failed: facts

*intent* maintenance · *language* de · *verified* True

> 1. Entfernen Sie den Motor von der Pumpenkörper, indem Sie die Verbindungsschrauben entfernen [p. 12].
> 2. Die Gleitringe und Lager prüfen, ob sie verschlissen oder beschädigt sind. Wenn sie beschädigt sind, sollten Sie sie wechseln [p. 5].
> 3. Warten Sie, bis der Motor und die Pumpenkörper abgekühlt sind, bevor Sie die Gleitringe und Lager wechseln [p. 5].
> 4. Den Gleitring mit einem neuen ersetzen und die Gleitringe sorgfältig reinigen, bevor Sie den Motor wieder einbauen [p. 5].
> 5. Den Motorlager mit einem neuen ersetzen und sorgfältig reinigen, bevor Sie den Motor wieder einbauen [p. 5].
> 6. Prüfen Sie, ob alle Teile ordnungsgemäß eingebaut sind, bevor Sie den Motor wieder einbauen [p. 5].
> 7. Die Pumpenkörper und Verbindungsschrauben wieder montieren [p. 12].
> 8. Die Pumpenkörper und Verbindungsschrauben wieder sichern [p. 12].
> 9. Die Pumpenkörper und Verbindungsschrauben wieder absichern [p. 12].
> 10. Die Pumpenkörper und Verbindungsschrauben wieder absichern [p. 12].
> 
> **Safety:** Wiederholen Sie die oben genannten Schritte, wenn Sie den Motor wieder einbauen [p. 8].

### `auto` · 16 s · failed: scope, intent, answer_language, page_cited, citations_valid, facts

*intent* out_of_scope · *language* de · *verified* True

> I can only help with technical questions about installing, starting up, maintaining and troubleshooting the pool equipment covered by the product manuals.

### `offline` · <0.1 s · failed: scope, intent, answer_language, page_cited, citations_valid, facts

*intent* out_of_scope · *language* de · *verified* True

> I can only help with technical questions about installing, starting up, maintaining and troubleshooting the pool equipment covered by the product manuals.

## q07 (en, typos): what shuold i do with the pump befor the winter if the pool is closed??

*Expected:* Empty the pump through the purge cap if it stays stopped, especially where it freezes (p. 11).

### `qwen` · 88 s · failed: page_cited, facts

*intent* maintenance · *language* en · *verified* True

> Before the winter, if the pool is closed and the pump stops working, you should:
> 
> 1. Check the junction box connections to ensure they are correct and tightened properly. [p. 13]
> 2. Verify the cables are correctly connected to the junction boxes. [p. 13]
> 3. Ensure the thermal protection is not tripping. [p. 13]
> 
> **Safety:** before any electrical or mechanical work, disconnect the pump from the mains, block all start-up devices, check there is no voltage and wait for the impeller to stop completely [p. 8]. Electrical work must be done by qualified personnel [p. 5].

### `llama` · 135 s

*intent* maintenance · *language* en · *verified* True

> Here are the steps to follow before winterizing the pump:
> 
> 1. Check the motor consumption and ensure it is equal to or below the manufacturer's rating plate value. If not, contact the Technical Assistance Service [p. 11].
> 2. Empty the pump if it is to remain at a standstill for a certain length of time, especially in cold countries where there is a risk of freezing [p. 11].
> 3. Remove the purge cap to empty the pump [p. 11].
> 4. Clean the pre-filter basket regularly to avoid drops in pressure [p. 11].
> 5. Check and clean the seal and its housing of any impurities when the pre-filter is opened [p. 12].
> 6. Replace the following components every 1 year:
> 	* Capacitor [p. 12]
> 	* Bearings [p. 12]
> 	* Mechanical seal [p. 12]
> 	* O-rings and other sealing components [p. 12]
> 7. If replacing the mechanical seal and/or bearings, replace the O-rings and sealing components as well [p. 12].
> 
> **Safety:** before any electrical or mechanical work, disconnect the pump from the mains, block all start-up devices, check there is no voltage and wait for the impeller to stop completely [p. 8]. Electrical work must be done by qualified personnel [p. 5].

### `gemma` · 146 s · failed: intent, page_cited, facts

*intent* troubleshooting · *language* en · *verified* True · *causes* Filter cap badly sealed

> 1. Clean the filter cap and check the condition of the rubber seal [p. 13].
> 2. Invert 2 power phases [p. 13].
> 
> **Safety:** before any electrical or mechanical work, disconnect the pump from the mains, block all start-up devices, check there is no voltage and wait for the impeller to stop completely [p. 8]. Electrical work must be done by qualified personnel [p. 5].

### `deepseek` · 130 s · failed: page_cited, facts

*intent* maintenance · *language* en · *verified* True

> 1. Ensure the pump is not installed in Zone 0 or Zone 1 as per the manual instructions on page 97.
> 2. Disconnect the pump from the power supply and start-up devices as per the safety instructions on page 5.
> 3. Avoid any electrical or mechanical work on the pump as per the safety warning on page 8.
> 4. Consult with your dealer or nearest dealer for any doubts regarding the installation or compliance with standards.
> 
> Safety: Before any electrical or mechanical work, disconnect the pump from the mains, block all start-up devices, check there is no voltage and wait for the impeller to stop completely [p. 8]. Electrical work must be done by qualified personnel [p. 5].

### `auto` · 95 s · failed: page_cited, facts

*intent* maintenance · *language* en · *verified* True

> Before the winter, you should do the following to prepare your pool pump for storage:
> 
> 1. Clean the seal and its housing of any impurities to ensure airtightness when the cap is closed (p. 12).
> 2. Replace the capacitor, bearings, and mechanical seal, as they suffer wear and tear due to normal use (p. 12).
> 3. Replace the O-rings and other sealing components (p. 12).
> 4. Disconnect the pump from the mains, block all start-up devices, check there is no voltage, and wait for the impeller to stop completely [p. 8]. Electrical work must be done by qualified personnel [p. 5].
> 
> **Safety:** before any electrical or mechanical work, disconnect the pump from the mains, block all start-up devices, check there is no voltage and wait for the impeller to stop completely [p. 8]. Electrical work must be done by qualified personnel [p. 5].

### `offline` · <0.1 s · failed: page_cited, facts

*intent* maintenance · *language* en · *verified* True

> From the ASTRAL Pool manual:
> - **3. Installation And Assembly > Location:** - Fit the pump below the water level in the pool to improve pump performance. - Make sure that the pump is safe from possible flooding and receives dry ventilation. [p. 9]
> - **Safety Information > Installation And Maintenance Information:** ... by children without supervision. • Our pumps may only be assembled and installed in pools that are compliant with standards  IEC / HD 60364-7-702  and required national rules. Should you have any doubts please consult your dealer. • The installation should follow standard IEC/HD 60364-7-702 and required national rules for swimming pools. • The pump can not be installed in the Zone 0 and Zone 1. To see drawings refer to page 97 . [p. 5]
> - **5. Maintenance:** - Every time the pre-filter is opened, clean the seal and its housing of any impurities to ensure airtightness when the cap is closed (Fig. 5). - Pump components that, due to their normal use, suffer wear and/or tear must be regularly re- placed to ensure good pump performance. The following table lists the fungible and / or consu- mable components of the pump and the period of time in which they must have been replaced. ... [p. 12]

## q08 (pt, clean): Como faço o arranque da bomba pela primeira vez?

*Expected:* First start-up: fill the pump with water through the pre-filter before starting (p. 11).

### `qwen` · 580 s · failed: page_cited

*intent* start_up · *language* pt · *verified* True

> 1. Verifique que a tensão e a frequência da rede elétrica correspondem às indicadas na etiqueta de referência do bomba (p. 11).
> 2. Verifique que o motor roda na direção correta usando a viseira atrás do motor (Fig. 6) (p. 11).
> 3. Certifique-se de que o motor está conectado à rede elétrica de forma segura, usando um múltiplo dispositivo de desconexão com uma distância de pelo menos 3 mm entre as superfícies (p. 9).
> 4. Verifique a instalação e a conexão da corrente de terra no equipamento (p. 10).
> 5. Certifique-se de que o motor está protegido por um motor guard e que a proteção magneto-termal está ativada (p. 10).
> 6. Verifique a instalação e a conexão da corrente de terra (p. 10).
> 7. Verifique a instalação e a conexão da corrente de terra (p. 10).
> 8. Verifique a instalação e a conexão da corrente de terra (p. 10).
> 
> **Safety:** antes de qualquer trabalho elétrico ou mecânico, desligue a bomba da rede, bloqueie todos os dispositivos de partida, verifique se não há tensão e aguarde até que o impulsionador pare completamente [p. 8]. Trabalhos elétricos devem ser feitos por profissionais qualificados [p. 5].

### `llama` · 163 s · failed: page_cited

*intent* start_up · *language* pt · *verified* True

> Para fazer o arranque da bomba pela primeira vez, siga os passos abaixo:
> 
> 1. Remova a tampa do pre-filtro desatando o parafuso que a segura no lugar (Fig. 5).
> 2. Encha a bomba com água através do pre-filtro até que ela suba pelo tubo de sucção.
> 3. Verifique se o filtro de sujeira foi removido e não esqueça reemplá-lo para evitar que partículas grandes entrem no pump e o bloqueiem.
> 4. Verifique que a tensão e frequência da corrente elétrica correspondam às indicadas na placa de rating da bomba.
> 5. Coloque a tampa do pre-filtro e fixe-a apertando bem, sem esquecer colocar o selante no seu local (Fig. 5).
> 6. Verifique se o motor gira na direção correta observando o fã localizado na parte traseira do motor, que pode ser visto através da abertura de visão no tapete do fã (Fig. 6).
> 7. Abra todas as válvulas e conecte o motor.
> 8. Ative o modo de auto-primagem e espere um tempo razoável para que ele seja concluído.
> 
> **Observação:** Se a bomba não estiver funcionando corretamente, é recomendável entrar em contato com o Serviço de Assistência Técnica.
> 
> **Segurança:** Antes de realizar qualquer trabalho elétrico ou mecânico, desconecte a bomba da tomada, bloqueie todos os dispositivos de início e verifique se não há tensão e espere até que o impellor pareça completamente [p. 8]. O trabalho elétrico deve ser realizado por pessoal qualificado [p. 5].

### `gemma` · 174 s · failed: intent, citations_valid

*intent* troubleshooting · *language* pt · *verified* True · *causes* Pre-filter blocked

> 1. Limpe a peneira pré-filtro (high) [p. 13].
> 2. Abra todas as válvulas e conecte o motor [p. 11, 4].
> 3. Ative o modo de auto-enchimento e aguarde um tempo razoável para a conclusão [p. 11, 4].
> 4. Se a bomba parar, verifique se o consumo em amperagem do motor em funcionamento é igual ou inferior ao indicado na placa do fabricante. Se esta informação não estiver disponível, contacte o Serviço de Assistência Técnica mais próximo [p. 11, 5].
> 
> **Safety:** before any electrical or mechanical work, disconnect the pump from the mains, block all start-up devices, check there is no voltage and wait for the impeller to stop completely [p. 8]. Electrical work must be done by qualified personnel [p. 5].

### `deepseek` · 75 s · failed: page_cited, citations_valid

*intent* installation · *language* pt · *verified* True

> 1. A primeira coisa a fazer é abrir todas as válvulas, incluindo qualquer válvula de bypass ou de recirculação, se houver.
> 2. Ligue o motor e certifique-se de que ele está conectado corretamente, conforme descrito no manual.
> 3. Ative o modo de auto-aspiração e aguarde um tempo razoável para que a aspiração seja completada.
> 4. Certifique-se de que todas as válvulas estão totalmente abertas e que não há obstruções que possam impedir a passagem de fluido.
> 5. Aguarde o suficiente para garantir que a bomba esteja operando sem problemas.
> 
> Se você estiver inseguro sobre como configurar a bomba, recomendamos entrar em contato com o Serviço de Assistência Técnica.

### `auto` · 194 s · failed: page_cited

*intent* start_up · *language* pt · *verified* True

> Para iniciar a bomba pela primeira vez, siga os seguintes passos:
> 
> 1. Verifique a conexão elétrica e certifique-se de que a tomada está adequada e segura. [p. 10]
> 2. Verifique a instalação e conexão do cabo de terra no equipamento. [p. 10]
> 3. Verifique a configuração do interruptor de curto-circuito de terra de acordo com a intensidade da bomba. [p. 10]
> 4. Verifique a configuração do fusível conforme a necessidade. [p. 10]
> 5. Desconecte a bomba da tomada de energia. [p. 8]
> 6. Verifique se há tensão no circuito. [p. 8]
> 7. Aguarde até que a bomba pare completamente. [p. 8]
> 8. Verifique se os componentes mecânicos, como os rolamentos e o selo mecânico, foram substituídos conforme o intervalo de tempo listado na tabela. [p. 12]
> 9. Verifique se os componentes plásticos, como os rolamentos e os selos, foram substituídos conforme o intervalo de tempo listado na tabela. [p. 12]
> 10. Verifique se os componentes plásticos, como os rolamentos e os selos, foram substituídos conforme o intervalo de tempo listado na tabela. [p. 12]
> 
> **Safety:** antes de qualquer trabalho elétrico ou mecânico, desconecte a bomba da tomada de energia, bloquee todos os dispositivos de iniciação, verifique se não há tensão e aguarde até que o impeller pare completamente [p. 8]. Trabalhos elétricos devem ser feitos por profissionais qualificados [p. 5].

### `offline` · <0.1 s · failed: intent, answer_language, page_cited, facts

*intent* general · *language* pt · *verified* True

> From the ASTRAL Pool manual:
> - **5. Maintenance:** ... Mechanical seal 1 year O-rings and other sealing components (1) 1 year (1) The opening and closing of the pump for the replacement of any of the inner spare parts does not guarantee the subsequent sealing. For this reason, it is recommended that the O-rings and sealing components are replaced whenever the mechanical seal and / or bearings are changed. ... [p. 12]
> - **3. Installation And Assembly > Electrical Installation:** ... power of the motor and to the length of the cable. For pumps with o three-phase motor: •  Use a motor guard with magneto-thermal protection. •  Protect the pump against overloads with a cut-off switch for the motor. •  Adjust the thermal value according to the thermal protection table. For the connection Δ (3 [p. 10]
> 
> **Safety:** before any electrical or mechanical work, disconnect the pump from the mains, block all start-up devices, check there is no voltage and wait for the impeller to stop completely [p. 8]. Electrical work must be done by qualified personnel [p. 5].

## q09 (es, out of scope): ¿Me recomiendas un buen restaurante en Barcelona?

*Expected:* Not about pool equipment: must be refused.

### `qwen` · 15 s

*intent* out_of_scope · *language* es · *verified* True

> I can only help with technical questions about installing, starting up, maintaining and troubleshooting the pool equipment covered by the product manuals.

### `llama` · 7.9 s

*intent* out_of_scope · *language* es · *verified* True

> I can only help with technical questions about installing, starting up, maintaining and troubleshooting the pool equipment covered by the product manuals.

### `gemma` · 16 s

*intent* out_of_scope · *language* es · *verified* True

> I can only help with technical questions about installing, starting up, maintaining and troubleshooting the pool equipment covered by the product manuals.

### `deepseek` · 7.2 s

*intent* out_of_scope · *language* es · *verified* True

> I can only help with technical questions about installing, starting up, maintaining and troubleshooting the pool equipment covered by the product manuals.

### `auto` · 12 s

*intent* out_of_scope · *language* es · *verified* True

> I can only help with technical questions about installing, starting up, maintaining and troubleshooting the pool equipment covered by the product manuals.

### `offline` · <0.1 s

*intent* out_of_scope · *language* en · *verified* True

> I can only help with technical questions about installing, starting up, maintaining and troubleshooting the pool equipment covered by the product manuals.

## q10 (en, not in manual): How many years of warranty does the ASTRAL pump have?

*Expected:* The manual never gives a warranty period: the answer must not invent a number of years. Refusing is also acceptable.

### `qwen` · 15 s

*intent* out_of_scope · *language* en · *verified* True

> I can only help with technical questions about installing, starting up, maintaining and troubleshooting the pool equipment covered by the product manuals.

### `llama` · 15 s

*intent* general · *language* en · *verified* True

> I could not find this in the available product manuals. Please contact the nearest Technical Assistance Service.

### `gemma` · 157 s

*intent* general · *language* en · *verified* True

> The manual does not specify the warranty period for the ASTRAL pump [p. 7]. It only states that unauthorized spare parts or accessories void the manufacturer’s liability [p. 7]. 
> 
> **Safety:** before any electrical or mechanical work, disconnect the pump from the mains, block all start-up devices, check there is no voltage and wait for the impeller to stop completely [p. 8]. Electrical work must be done by qualified personnel [p. 5].

### `deepseek` · 6.7 s

*intent* out_of_scope · *language* en · *verified* True

> I can only help with technical questions about installing, starting up, maintaining and troubleshooting the pool equipment covered by the product manuals.

### `auto` · 12 s

*intent* out_of_scope · *language* en · *verified* True

> I can only help with technical questions about installing, starting up, maintaining and troubleshooting the pool equipment covered by the product manuals.

### `offline` · <0.1 s · failed: says_not_in_manual

*intent* general · *language* en · *verified* True

> From the ASTRAL Pool manual:
> - **5. Maintenance:** ... placed to ensure good pump performance. The following table lists the fungible and / or consu- mable components of the pump and the period of time in which they must have been replaced. DESCRIPTION OF THE COMPONENT TIME BETWEEN REPLACEMENTS Capacitor 1 year Bearings 1 year Mechanical seal 1 year O-rings and other sealing components (1) 1 year (1) The opening and closing of the pump for the replacement of any of the inner spare parts does not ... [p. 12]
> - **Safety Information > Installation And Maintenance Information:** ... • All assembly, electrical installation and maintenance work must be carried out by qualified, authorized personnel who have carefully read the installation and service instructions. • This appliance is not intended for use by persons (including children) with reduced physical, sensory or mental capabilities, or lack of experience and knowledge, unless they have been given supervision or instruction concerning ... [p. 5]
> - **3. Installation And Assembly > Electrical Installation:** ... - Respect the electrical installation and connection instructions. Failure to do so may lead to the pump's manufacturer declining all liability and rendering the warranty null and void. - The installation may be subject to special regulations. - Unsuitable mains connections involve the risk of electrocution. For pumps with a single-phase motor: •  Thermal protection is incorporated. •  Use a motor guard with magneto-thermal protection. ... [p. 10]
> 
> **Safety:** before any electrical or mechanical work, disconnect the pump from the mains, block all start-up devices, check there is no voltage and wait for the impeller to stop completely [p. 8]. Electrical work must be done by qualified personnel [p. 5].
