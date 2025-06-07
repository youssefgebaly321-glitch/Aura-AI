// --- web/js/audio_processor.js ---

/**
 * An AudioWorkletProcessor that converts float32 audio data to 16-bit PCM
 * and posts it back to the main thread.
 */
class PCMProcessor extends AudioWorkletProcessor {
    constructor() {
        super();
    }

    process(inputs, outputs, parameters) {
        // The 'inputs' array contains an array of inputs, each with its own channels.
        // We will mix all channels from all inputs down to a single mono channel.
        const output = new Float32Array(inputs[0][0].length);
        let channelCount = 0;

        for (const input of inputs) {
            for (const channel of input) {
                if (channel.length === output.length) {
                    for (let i = 0; i < channel.length; i++) {
                        output[i] += channel[i];
                    }
                    channelCount++;
                }
            }
        }

        if (channelCount === 0) {
            return true; // No data to process
        }
        
        // Average the mixed channels
        for (let i = 0; i < output.length; i++) {
            output[i] /= channelCount;
        }
        
        // Convert the mixed Float32Array to a 16-bit PCM Int16Array
        const pcmData = new Int16Array(output.length);
        for (let i = 0; i < output.length; i++) {
            const s = Math.max(-1, Math.min(1, output[i]));
            pcmData[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }

        // Post the raw PCM data buffer back to the main thread.
        // The second argument is a list of transferable objects.
        this.port.postMessage(pcmData.buffer, [pcmData.buffer]);

        return true; // Keep the processor alive and running
    }
}

registerProcessor('pcm-processor', PCMProcessor);