import { NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

export async function GET() {
  // Read environment variable at request time, not module load time
  const canChangeKeys = process.env.CAN_CHANGE_KEYS !== "false";
  return NextResponse.json({ canChange: canChangeKeys })
}