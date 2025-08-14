import express from 'express';
import { getClientNotificationsByClientId } from '../controllers/clientNotificationController.js';

const router = express.Router();

router.get('/:clientId', getClientNotificationsByClientId);

export default router;