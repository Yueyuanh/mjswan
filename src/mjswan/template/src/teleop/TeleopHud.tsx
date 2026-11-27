import { Box, Divider, Flex, Paper, Text } from '@mantine/core';

/** One key, filled while it is held. */
function Keycap({ label, pressed = false }: { label: string; pressed?: boolean }) {
  return (
    <Box
      aria-hidden
      style={{
        width: '1.6em',
        height: '1.6em',
        display: 'grid',
        placeItems: 'center',
        borderRadius: '0.25em',
        border: '1px solid',
        borderColor: pressed ? 'var(--mantine-primary-color-filled)' : 'var(--mantine-color-default-border)',
        background: pressed ? 'var(--mantine-primary-color-filled)' : 'var(--mantine-color-default)',
        color: pressed ? 'var(--mantine-primary-color-contrast)' : 'var(--mantine-color-text)',
        fontFamily: 'var(--mantine-font-family-monospace)',
        fontSize: '0.72em',
        fontWeight: 600,
        lineHeight: 1,
        transition: 'background-color 60ms linear, border-color 60ms linear',
      }}
    >
      {label}
    </Box>
  );
}

function signed(value: number): string {
  const rounded = Number(value.toFixed(2));
  return `${rounded < 0 ? '' : '+'}${rounded.toFixed(2)}`;
}

/** The key legend at the top left: what each key does and what it commands now. */
export function TeleopHud({
  held,
  vx,
  vy,
  vz,
  hasPosture,
  biped,
  transitioning,
}: {
  held: ReadonlySet<string>;
  vx: number;
  vy: number;
  vz: number;
  hasPosture: boolean;
  biped: boolean;
  transitioning: boolean;
}) {
  const posture = transitioning
    ? `Switching to ${biped ? 'biped' : 'crawl'}…`
    : biped
      ? 'Biped'
      : 'Crawl';
  return (
    <Paper
      withBorder
      radius="sm"
      shadow="sm"
      style={{
        position: 'absolute',
        top: '1em',
        left: '1em',
        zIndex: 5,
        padding: '0.6em 0.75em',
        pointerEvents: 'none',
        background: 'color-mix(in srgb, var(--mantine-color-body) 78%, transparent)',
        backdropFilter: 'blur(8px)',
        fontSize: '0.8rem',
        lineHeight: 1.2,
      }}
    >
      <Flex gap="0.6em" align="flex-start">
        <Box style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
          <Flex gap={2}>
            <Keycap label="Q" pressed={held.has('KeyQ')} />
            <Keycap label="E" pressed={held.has('KeyE')} />
          </Flex>
          <Keycap label="W" pressed={held.has('KeyW')} />
          <Flex gap={2}>
            <Keycap label="A" pressed={held.has('KeyA')} />
            <Keycap label="S" pressed={held.has('KeyS')} />
            <Keycap label="D" pressed={held.has('KeyD')} />
          </Flex>
        </Box>
        <Box pt={2}>
          <Text fw={600} style={{ fontSize: '0.85em' }}>
            Move / Turn
          </Text>
          <Text
            c="dimmed"
            style={{ fontFamily: 'var(--mantine-font-family-monospace)', fontSize: '0.78em' }}
          >
            vx {signed(vx)} · vy {signed(vy)} m/s
          </Text>
          <Text
            c="dimmed"
            style={{ fontFamily: 'var(--mantine-font-family-monospace)', fontSize: '0.78em' }}
          >
            wz {signed(vz)} rad/s
          </Text>
          <Text c="dimmed" style={{ fontSize: '0.72em' }}>
            75% of each axis's limit
          </Text>
        </Box>
      </Flex>
      <Divider my="0.45em" />
      <Flex direction="column" gap={4}>
        {hasPosture && (
          <Flex align="center" gap="0.45em">
            <Keycap label="F" />
            <Text style={{ fontSize: '0.8em' }}>Posture: {posture}</Text>
          </Flex>
        )}
        <Flex align="center" gap="0.45em">
          <Keycap label="X" />
          <Text style={{ fontSize: '0.8em' }}>Skin view</Text>
        </Flex>
        <Flex align="center" gap="0.45em">
          <Keycap label="Z" />
          <Text style={{ fontSize: '0.8em' }}>Sidebar</Text>
        </Flex>
        <Flex align="center" gap="0.45em">
          <Keycap label="R" />
          <Text style={{ fontSize: '0.8em' }}>Reset</Text>
        </Flex>
      </Flex>
      <Text c="dimmed" style={{ fontSize: '0.7em', marginTop: '0.45em' }}>
        W+A / W+D combine; W+S, A+D or Q+E cancel
      </Text>
    </Paper>
  );
}
