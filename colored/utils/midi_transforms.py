#!/usr/bin/env python3
"""
🎵 MIDI Transformations - Port-specific MIDI modifications
========================================================
Apply different transformations to MIDI data for different OSC ports

Author: AI Assistant
Date: 2025-01-08
"""

from typing import List, Dict, Tuple, Any


def transform_midi_for_port(notes: List[int], 
                          velocities: List[int], 
                          durations: List[int], 
                          port_config: Dict[str, Any]) -> Tuple[List[int], List[int], List[int]]:
    """
    Transform MIDI data based on port-specific configuration
    
    Args:
        notes: List of MIDI note numbers (21-127)
        velocities: List of velocity values (1-127)
        durations: List of duration values in milliseconds
        port_config: Configuration dict for this port containing:
            - note_offset: Semitones to shift notes (+/-)
            - velocity_multiplier: Factor to multiply velocities
            - duration_multiplier: Factor to multiply durations
    
    Returns:
        Tuple of (transformed_notes, transformed_velocities, transformed_durations)
    """
    if not notes or not velocities or not durations:
        return notes, velocities, durations
    
    # Extract transformation parameters
    note_offset = port_config.get('note_offset', 0)
    velocity_multiplier = port_config.get('velocity_multiplier', 1.0)
    duration_multiplier = port_config.get('duration_multiplier', 1.0)
    
    # Transform notes (with MIDI range clamping)
    transformed_notes = []
    for note in notes:
        new_note = note + note_offset
        # Clamp to valid MIDI range (21-127, full piano range)
        clamped_note = max(21, min(127, new_note))
        transformed_notes.append(clamped_note)
    
    # Transform velocities (with MIDI range clamping)
    transformed_velocities = []
    for velocity in velocities:
        new_velocity = int(velocity * velocity_multiplier)
        # Clamp to valid MIDI velocity range (1-127)
        clamped_velocity = max(1, min(127, new_velocity))
        transformed_velocities.append(clamped_velocity)
    
    # Transform durations (with reasonable minimum)
    transformed_durations = []
    for duration in durations:
        new_duration = int(duration * duration_multiplier)
        # Clamp to reasonable range (minimum 50ms, maximum 10000ms)
        clamped_duration = max(50, min(10000, new_duration))
        transformed_durations.append(clamped_duration)
    
    return transformed_notes, transformed_velocities, transformed_durations


def apply_transformations_to_ports(base_notes: List[int],
                                 base_velocities: List[int], 
                                 base_durations: List[int],
                                 osc_ports: List[int],
                                 osc_clients: List[Any],
                                 config: Dict[str, Any],
                                 send_midi_func) -> int:
    """
    Apply port-specific transformations and send MIDI to all clients
    
    Args:
        base_notes: Original MIDI notes
        base_velocities: Original velocities  
        base_durations: Original durations
        osc_ports: List of OSC port numbers
        osc_clients: List of OSC client objects
        config: Full configuration dict containing port_transformations
        send_midi_func: Function to send MIDI (e.g., send_midi from osc_utils)
    
    Returns:
        Number of successful transmissions
    """
    if not base_notes or not base_velocities or not base_durations:
        return 0
    
    port_transformations = config.get('port_transformations', {})
    transmission_count = 0
    
    for port, client in zip(osc_ports, osc_clients):
        port_str = str(port)
        
        # Get transformation config for this port (default to passthrough)
        if port_str in port_transformations:
            port_config = port_transformations[port_str]
        else:
            # Default passthrough config for unknown ports
            port_config = {
                'note_offset': 0,
                'velocity_multiplier': 1.0,
                'duration_multiplier': 1.0,
                'name': 'default'
            }
        
        # Apply transformations
        transformed_notes, transformed_vels, transformed_durs = transform_midi_for_port(
            base_notes, base_velocities, base_durations, port_config
        )
        
        # Send transformed MIDI
        try:
            send_midi_func(client, len(transformed_notes), transformed_notes, transformed_vels, transformed_durs)
            transmission_count += 1
            
            # Debug output for first few frames or when significant transformations occur
            if port_config.get('note_offset', 0) != 0 or port_config.get('velocity_multiplier', 1.0) != 1.0:
                print(f"🎼 Port {port} ({port_config.get('name', 'unknown')}): "
                      f"{len(transformed_notes)} notes, "
                      f"offset: {port_config.get('note_offset', 0)}, "
                      f"vel×{port_config.get('velocity_multiplier', 1.0):.1f}, "
                      f"dur×{port_config.get('duration_multiplier', 1.0):.1f}")
                      
        except Exception as e:
            print(f"❌ Port {port} 전송 실패: {e}")
    
    return transmission_count


def get_port_transformation_info(config: Dict[str, Any]) -> Dict[str, str]:
    """
    Get human-readable information about port transformations
    
    Args:
        config: Configuration dict containing port_transformations
        
    Returns:
        Dict mapping port numbers to description strings
    """
    port_transformations = config.get('port_transformations', {})
    info = {}
    
    for port_str, port_config in port_transformations.items():
        name = port_config.get('name', 'unknown')
        description = port_config.get('description', '')
        note_offset = port_config.get('note_offset', 0)
        vel_mult = port_config.get('velocity_multiplier', 1.0)
        dur_mult = port_config.get('duration_multiplier', 1.0)
        
        info[port_str] = f"{name}: {description} (notes{note_offset:+d}, vel×{vel_mult:.1f}, dur×{dur_mult:.1f})"
    
    return info