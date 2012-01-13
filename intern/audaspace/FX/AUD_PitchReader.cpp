/*
 * ***** BEGIN GPL LICENSE BLOCK *****
 *
 * Copyright 2009-2011 Jörg Hermann Müller
 *
 * This file is part of AudaSpace.
 *
 * Audaspace is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * AudaSpace is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Audaspace; if not, write to the Free Software Foundation,
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file audaspace/FX/AUD_PitchReader.cpp
 *  \ingroup audfx
 */


#include "AUD_PitchReader.h"

AUD_PitchReader::AUD_PitchReader(AUD_Reference<AUD_IReader> reader, float pitch) :
		AUD_EffectReader(reader), m_pitch(pitch)
{
}

AUD_Specs AUD_PitchReader::getSpecs() const
{
	AUD_Specs specs = m_reader->getSpecs();
	specs.rate *= m_pitch;
	return specs;
}

float AUD_PitchReader::getPitch() const
{
	return m_pitch;
}

void AUD_PitchReader::setPitch(float pitch)
{
	m_pitch = pitch;
}