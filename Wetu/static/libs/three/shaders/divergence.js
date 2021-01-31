define([], function() {
	return shader = `

varying vec2 vUv;
uniform float alpha;
uniform float threshold;
uniform float threshold2;
uniform vec2 resolution;
uniform sampler2D tDiffuse;

vec2 sample_grad(vec2 vUv) {
    float t = texture2D(tDiffuse, vUv).x;
    float dx = texture2D(tDiffuse, vUv - vec2(1., 0.) / resolution).x - t;
    float dy = texture2D(tDiffuse, vUv - vec2(0., 1.) / resolution).x - t;
    // float dx = texture2D(tDiffuse, vUv - vec2(1., 0.) / resolution).x - texture2D(tDiffuse, vUv + vec2(1., 0.) / resolution).x;
    // float dy = texture2D(tDiffuse, vUv - vec2(0., 1.) / resolution).x - texture2D(tDiffuse, vUv + vec2(0., 1.) / resolution).x;
    return vec2(dx, dy);
}

float divergence1() {

    float dsum = 0., wsum = 0.;
    
    const float w[3] = float[3](1., 2., 1.);
    float h = 0.5;
    
    // for each texel in a 3x3 neighborhood centered on this one
    for (int i=0; i<3; ++i) {
        for (int j=0; j<3; ++j) {
            
            // offset to neighbor texel
            vec2 delta = h*(vec2(float(i),float(j))-1.);

            // fetch gradient & distance at neighbor
            vec2 grad = sample_grad(vUv + delta / resolution);
            
            float wij = w[i]*w[j];
            
            dsum += wij * dot(delta, grad);
            wsum += wij;     
               
        }
    }

    float divergence = alpha * dsum / (wsum);
    return divergence;
}

float divergence2() {
    float dx = texture2D(tDiffuse, vUv - vec2(1., 0.) / resolution).x - texture2D(tDiffuse, vUv + vec2(1., 0.) / resolution).x;
    float dy = texture2D(tDiffuse, vUv - vec2(0., 1.) / resolution).x - texture2D(tDiffuse, vUv + vec2(0., 1.) / resolution).x;
    return dx + dy;
}

float divergence3() {
    // const float e = 0.01;
    float t = texture2D(tDiffuse, vUv).x;
    bool dx = texture2D(tDiffuse, vUv - vec2(1., 0.) / resolution).x < t && texture2D(tDiffuse, vUv + vec2(1., 0.) / resolution).x < t;
    bool dy = texture2D(tDiffuse, vUv - vec2(0., 1.) / resolution).x < t && texture2D(tDiffuse, vUv + vec2(0., 1.) / resolution).x < t;
    return t > 0.01 && (dx || dy) ? 1. : 0.;
}

void main()	{

    // float t = texture2D(tDiffuse, vUv).x;
    // divergence = t < 0.01 ? 1.0 : divergence;
    // divergence = divergence < threshold ? 1.0 : 0.0;
    // divergence = abs(divergence) < 0.01 ? 1.0 : 0.0;
    // divergence += 0.5;
    // divergence = 1. - abs(2. * divergence);
    // divergence = max(abs(5. * divergence), 0.);
    // divergence = divergence < 0.05 ? 0. : 1.;
    
    // divergence = pow(divergence, 2.);

    // // Working method 1:
    float divergence = divergence1();
    float t = texture2D(tDiffuse, vUv).x;
    divergence = 1. - smoothstep(0.0, 1.0, divergence);
    divergence = t < 0.1 ? 1. : divergence;

    // Simply watch change of sign
    // float divergence = divergence3();

	gl_FragColor = vec4(divergence, divergence, divergence, 1.);
}`});
