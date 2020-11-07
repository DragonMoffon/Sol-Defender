#version 330

uniform float time;

uniform vec2 mod_pos;

// (x, y) position passed in
in vec2 in_pos;

in vec2 in_vel;

in float in_fade;

// Output the color to the fragment shader
out vec4 color;

void main() {

    // Set the RGBA color
    float alpha = 1.0 - (in_fade * time);
    if(alpha < 0.0) alpha = 0;

    color = vec4(0.00, 0.76, 1.00, alpha);

    vec2 new_vel = in_vel;

    vec2 new_pos = in_pos + (time * new_vel);

    // Set the position. (x, y, z, w)
    gl_Position = vec4(new_pos + mod_pos, 0, 1);
}