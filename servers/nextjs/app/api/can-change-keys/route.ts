import { NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

// ponytail: TubeOnAI's embed has no presenton-native login session, so we
// intentionally skip upstream's authStatusForRequest()/admin-role gate here
// (it would always evaluate to unauthenticated for our iframe users and
// permanently disable key changes). Gate purely on the deployment env var.
export async function GET() {
  // Read environment variable at request time, not module load time
  const canChangeKeys = process.env.CAN_CHANGE_KEYS !== "false";
  return NextResponse.json({ canChange: canChangeKeys })
}
