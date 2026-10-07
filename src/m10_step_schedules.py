"""Viggle Turbo node refinement: retain trained low-noise nodes.
https://huggingface.co/Viggle/Qwen-Image-2.1-viggle-turbo
Changing num_inference_steps alone while passing six sigmas still yields six steps.
"""
FIXED_NODES=(.875,.75,.5,.25)
def turbo_sigmas(steps):
    if not isinstance(steps,int) or isinstance(steps,bool) or steps<5:
        raise ValueError('At least five steps are required for this schedule')
    high_count=steps-len(FIXED_NODES)
    return [1.-.125*i/high_count for i in range(high_count)]+list(FIXED_NODES)
